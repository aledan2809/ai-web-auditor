"""
AI Web Auditor — AVE Landing API Router v1
Endpoints consumed by the AVE landing page (techbiz.ae/ave/).
Reference: API_CONTRACTS_AUDITOR_v1.md
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from database.connection import get_db
from database.models import Audit, Lead, AuditLog
from services.pricing import get_current_pricing, seed_default_pricing
from services.scoring import (
    ComponentId, from_legacy_scores, compute_overall_score,
    overall_result_to_dict, score_status,
)

router = APIRouter(prefix="/api/audit", tags=["ave-landing"])


# ── Schemas ──────────────────────────────────────────────────────────

class AveStartRequest(BaseModel):
    websiteUrl: str
    email: Optional[str] = None
    market: str = "UAE"


class AveUnlockRequest(BaseModel):
    email: EmailStr
    firstName: Optional[str] = None
    phone: Optional[str] = None
    consent: dict  # { privacyAccepted, marketingOptIn, timestamp }


# ── Helpers ──────────────────────────────────────────────────────────

def _generate_id(prefix: str = "aud") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _build_teaser_components(audit) -> List[dict]:
    """Build 3 teaser component cards from legacy audit scores."""
    components = []

    if audit.performance_score is not None:
        components.append({
            "componentId": "PERF",
            "name": "Core Web Vitals",
            "score": audit.performance_score,
            "status": score_status(audit.performance_score),
            "previewIssues": [],
            "hiddenIssuesCount": 0,
        })

    if audit.seo_score is not None:
        components.append({
            "componentId": "OPSEO",
            "name": "On-Page SEO",
            "score": audit.seo_score,
            "status": score_status(audit.seo_score),
            "previewIssues": [],
            "hiddenIssuesCount": 0,
        })

    if audit.security_score is not None:
        components.append({
            "componentId": "SEC",
            "name": "Security",
            "score": audit.security_score,
            "status": score_status(audit.security_score),
            "previewIssues": [],
            "hiddenIssuesCount": 0,
        })

    # Fill preview issues from audit issues
    from sqlalchemy import select as sel
    # Issues will be populated later when we have the DB session
    return components[:3]


async def _populate_preview_issues(db: AsyncSession, audit_id: str, components: List[dict]):
    """Attach up to 3 preview issues per component from DB."""
    from database.models import AuditIssue

    result = await db.execute(
        select(AuditIssue)
        .where(AuditIssue.audit_id == audit_id)
        .order_by(AuditIssue.severity)
        .limit(30)
    )
    issues = result.scalars().all()

    # Map issue categories to component IDs
    cat_map = {
        "performance": "PERF",
        "seo": "OPSEO",
        "security": "SEC",
        "gdpr": "PRIV",
        "accessibility": "A11Y",
        "ui_ux": "MOBUX",
        "full": "COMP",
    }

    for comp in components:
        comp_id = comp["componentId"]
        matching = [
            i for i in issues
            if cat_map.get(i.category, "") == comp_id
        ]
        comp["previewIssues"] = [
            {
                "issueId": f"{comp_id}-{idx:03d}",
                "severity": i.severity.upper() if i.severity else "MEDIUM",
                "title": i.title,
                "oneLineImpact": (i.description or "")[:120],
                "confidenceScore": 0.85,
            }
            for idx, i in enumerate(matching[:3])
        ]
        comp["hiddenIssuesCount"] = max(0, len(matching) - 3)


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/start")
async def ave_start_audit(
    request: AveStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new AVE audit (landing page flow).
    Accepts websiteUrl + optional email.
    Returns auditId + teaserUrl + pricing.
    """
    from repositories.audit_repo import AuditRepository

    url = request.websiteUrl.strip()
    if not url.startswith("http"):
        url = "https://" + url

    audit_repo = AuditRepository(db)
    audit = await audit_repo.create(
        url=url,
        audit_types=["full"],
        user_id=None,
    )

    # Import and run audit in background
    from main import run_audit
    background_tasks.add_task(
        run_audit, audit.id, url, ["full"], True, True, "en"
    )

    # Get pricing
    await seed_default_pricing(db)
    pricing = await get_current_pricing(db, request.market)

    return {
        "auditId": audit.id,
        "teaserUrl": f"/audit/{audit.id}/teaser",
        "pricing": {
            "isCampaign": pricing["isCampaign"],
            "freeComponents": 3,
            "unlockPriceAED": pricing["unlockPriceAED"],
            "fullPriceAED": pricing.get("normalFullPriceAED"),
            "normalUnlockPriceAED": pricing["normalUnlockPriceAED"],
            "normalFullPriceAED": pricing.get("normalFullPriceAED"),
            "endsAt": pricing.get("campaignEndsAt"),
        },
        "catalogVersion": "v1",
        "reportContractVersion": "v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{audit_id}/teaser")
async def ave_get_teaser(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get teaser report (3 free components).
    Landing page polls this after starting an audit.
    """
    result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # If still running, return status
    if audit.status in ("pending", "running"):
        return {
            "auditId": audit_id,
            "status": audit.status,
            "isTeaser": True,
            "isUnlocked": False,
            "message": "Audit is still running. Poll again in a few seconds.",
        }

    # Build component scores using the new scoring engine
    comp_scores = from_legacy_scores(
        performance_score=audit.performance_score,
        seo_score=audit.seo_score,
        security_score=audit.security_score,
        gdpr_score=audit.gdpr_score,
        accessibility_score=audit.accessibility_score,
        mobile_ux_score=getattr(audit, 'mobile_ux_score', None),
        trust_score=getattr(audit, 'trust_score', None),
        competitor_score=getattr(audit, 'competitor_score', None),
    )
    overall = compute_overall_score(comp_scores)

    # Build teaser components (max 3)
    components = _build_teaser_components(audit)
    await _populate_preview_issues(db, audit_id, components)

    # Count total hidden issues
    from database.models import AuditIssue
    issue_count_result = await db.execute(
        select(AuditIssue).where(AuditIssue.audit_id == audit_id)
    )
    total_issues = len(issue_count_result.scalars().all())
    shown_issues = sum(len(c.get("previewIssues", [])) for c in components)

    # Get pricing
    pricing = await get_current_pricing(db, "UAE")

    return {
        "auditId": audit_id,
        "websiteUrl": audit.url,
        "isTeaser": True,
        "isUnlocked": False,
        "overallScore": overall.overall_score,
        "overallStatus": overall.overall_status,
        "components": components,
        "hiddenIssuesCount": max(0, total_issues - shown_issues),
        "pricing": {
            "unlockPriceAED": pricing["unlockPriceAED"],
            "endsAt": pricing.get("campaignEndsAt"),
        },
        "catalogVersion": "v1",
        "reportContractVersion": "v1",
        "issueLibraryVersion": "v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{audit_id}/unlock")
async def ave_unlock(
    audit_id: str,
    request: AveUnlockRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Unlock full report (lead capture with consent).
    Stores lead, returns full report + PDF URLs.
    """
    result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Validate consent
    if not request.consent.get("privacyAccepted"):
        raise HTTPException(status_code=400, detail="CONSENT_REQUIRED")

    # Create lead record
    lead_id = _generate_id("lead")
    now = datetime.now(timezone.utc)
    ref = f"AVE-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    lead = Lead(
        id=lead_id,
        reference=ref,
        email=request.email,
        name=request.firstName or "",
        audit_id=audit_id,
        url=audit.url,
        terms_accepted_at=now,
        marketing_consent=request.consent.get("marketingOptIn", False),
    )
    db.add(lead)

    # Audit log for consent
    log = AuditLog(
        action="unlock_consent",
        entity_type="lead",
        entity_id=lead_id,
        email=request.email,
        details={
            "auditId": audit_id,
            "consent": request.consent,
        },
    )
    db.add(log)
    await db.commit()

    # Send admin notification (non-blocking)
    email_sent = False
    try:
        from services.email_service import send_admin_unlock
        email_sent = send_admin_unlock(audit.url, audit_id, request.email, lead_id)
    except Exception as e:
        print(f"Unlock notification error: {e}")

    return {
        "auditId": audit_id,
        "leadId": lead_id,
        "fullReportUrl": f"/audit/{audit_id}/full",
        "pdfUrl": f"/api/reports/pdf?auditId={audit_id}",
        "emailSent": email_sent,
        "catalogVersion": "v1",
        "reportContractVersion": "v1",
        "issueLibraryVersion": "v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{audit_id}/full")
async def ave_get_full_report(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full online report (9 components, all issues).
    Only available after unlock.
    """
    result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Check if unlocked (has a lead record)
    lead_result = await db.execute(select(Lead).where(Lead.audit_id == audit_id).limit(1))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=403, detail="Report not unlocked. Submit email first.")

    # Build full scoring
    comp_scores = from_legacy_scores(
        performance_score=audit.performance_score,
        seo_score=audit.seo_score,
        security_score=audit.security_score,
        gdpr_score=audit.gdpr_score,
        accessibility_score=audit.accessibility_score,
        mobile_ux_score=getattr(audit, 'mobile_ux_score', None),
        trust_score=getattr(audit, 'trust_score', None),
        competitor_score=getattr(audit, 'competitor_score', None),
    )
    overall = compute_overall_score(comp_scores)
    overall_dict = overall_result_to_dict(overall)

    # Get all issues
    from database.models import AuditIssue
    issues_result = await db.execute(
        select(AuditIssue).where(AuditIssue.audit_id == audit_id)
    )
    all_issues = issues_result.scalars().all()

    # Build top 10 issues
    top10 = sorted(all_issues, key=lambda i: _severity_order(i.severity))[:10]

    # Get pricing
    pricing = await get_current_pricing(db, "UAE")

    return {
        "auditId": audit_id,
        "websiteUrl": audit.url,
        "isTeaser": False,
        "isUnlocked": True,
        "overall": {
            "overallScore": overall_dict["overallScore"],
            "overallStatus": overall_dict["overallStatus"],
            "topRisks": overall_dict["topRisks"][:3],
        },
        "components": overall_dict["components"],
        "top10Issues": [
            {
                "issueId": f"{i.category.upper()}-{idx:03d}" if i.category else f"ISSUE-{idx:03d}",
                "componentId": _cat_to_component(i.category),
                "severity": i.severity.upper() if i.severity else "MEDIUM",
                "title": i.title,
                "description": i.description,
                "recommendation": i.recommendation,
                "timeEstimate": f"{i.estimated_hours:.0f}h" if i.estimated_hours else "1h",
                "complexity": i.complexity or "medium",
                "confidenceScore": 0.85,
            }
            for idx, i in enumerate(top10)
        ],
        "totalIssues": len(all_issues),
        "pricing": {
            "quickWinsBundleAED": pricing["quickWinsPriceAED"],
            "monitorTier1MonthlyAED": pricing["monitorMonthlyAED"],
        },
        "catalogVersion": "v1",
        "reportContractVersion": "v1",
        "issueLibraryVersion": "v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def _severity_order(severity: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(
        (severity or "medium").lower(), 2
    )


def _cat_to_component(category: str) -> str:
    return {
        "performance": "PERF",
        "seo": "OPSEO",
        "security": "SEC",
        "gdpr": "PRIV",
        "accessibility": "A11Y",
        "ui_ux": "MOBUX",
        "full": "COMP",
    }.get((category or "").lower(), "OPSEO")
