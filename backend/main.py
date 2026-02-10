"""
AI Web Auditor - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
import os

from sqlalchemy.ext.asyncio import AsyncSession

# Database
from database.connection import get_db, init_db, close_db
from database.models import User, Audit

# Repositories
from repositories.user_repo import UserRepository
from repositories.audit_repo import AuditRepository

# Auth
from auth.router import router as auth_router
from auth.dependencies import get_current_user, get_current_user_optional

# Payments
from payments.router import router as payments_router

# Admin
from admin.router import router as admin_router

# Leads
from leads.router import router as leads_router

# Settings
from settings.router import router as settings_router

# Competitors
from competitors.router import router as competitors_router

# Marketing
from marketing.router import router as marketing_router

# AI Agents
from ai.agents.router import router as ai_agents_router

# AVE Landing endpoints (teaser/unlock/full)
from services.ave_router import router as ave_router

# Schemas
from models.schemas import (
    AuditRequest, AuditResponse, AuditResult, AuditStatus,
    AuditType, EstimateRequest, PriceEstimate, APITestRequest,
    AuditIssue, PerformanceMetrics, SEOMetrics, SecurityMetrics,
    GDPRMetrics, AccessibilityMetrics
)


# ============== LIFESPAN ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    import asyncio

    # Startup
    print("Starting AI Web Auditor API...")
    await init_db()
    print("Database initialized")

    # Start email scheduler in background
    from services.email_scheduler import run_email_scheduler_loop
    scheduler_task = asyncio.create_task(run_email_scheduler_loop())

    yield

    # Shutdown
    scheduler_task.cancel()
    print("Shutting down...")
    await close_db()


# ============== APP INITIALIZATION ==============

app = FastAPI(
    title="AI Web Auditor API",
    description="Comprehensive website auditing platform with AI analysis",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://frontend-eosin-seven-27.vercel.app",
        "https://frontend-mbhvxomt4-alex-danciulescus-projects.vercel.app",
        "https://www.techbiz.ae",
        "https://techbiz.ae",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(leads_router)
app.include_router(settings_router)
app.include_router(competitors_router)
app.include_router(marketing_router)
app.include_router(ai_agents_router)
app.include_router(ave_router)


# ============== BASIC ENDPOINTS ==============

@app.get("/")
async def root():
    return {
        "name": "AI Web Auditor API",
        "version": "2.0.0",
        "status": "online"
    }


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============== AUDIT ENDPOINTS ==============

@app.post("/api/audit/start", response_model=AuditResponse)
async def start_audit(
    request: AuditRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Start a new website audit"""
    audit_repo = AuditRepository(db)

    # Check credits if user is authenticated
    if current_user:
        if current_user.credits <= 0:
            raise HTTPException(
                status_code=402,
                detail="Credite insuficiente. Achizitionati mai multe credite pentru a continua."
            )
        # Deduct credit
        user_repo = UserRepository(db)
        await user_repo.deduct_credit(current_user.id)

    # Create audit record
    audit = await audit_repo.create(
        url=str(request.url),
        audit_types=[t.value for t in request.audit_types],
        user_id=current_user.id if current_user else None
    )

    # Start audit in background
    background_tasks.add_task(
        run_audit,
        audit.id,
        str(request.url),
        [t.value for t in request.audit_types],
        request.include_screenshots,
        request.mobile_test,
        request.lang
    )

    return AuditResponse(
        success=True,
        audit_id=audit.id,
        message="Audit started successfully",
        status=AuditStatus.PENDING
    )


@app.get("/api/audit/{audit_id}")
async def get_audit(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get audit status and results"""
    audit_repo = AuditRepository(db)
    audit = await audit_repo.get_by_id(audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit negasit")

    # Build response
    issues = []
    for issue in audit.issues:
        issues.append(AuditIssue(
            id=issue.id,
            category=AuditType(issue.category) if issue.category in [t.value for t in AuditType] else AuditType.FULL,
            severity=issue.severity,
            title=issue.title,
            description=issue.description or "",
            recommendation=issue.recommendation or "",
            affected_element=issue.affected_element,
            estimated_hours=issue.estimated_hours,
            complexity=issue.complexity
        ))

    # Build metrics
    performance_metrics = None
    if audit.performance_metrics:
        pm = audit.performance_metrics
        performance_metrics = PerformanceMetrics(
            score=pm.score,
            lcp=pm.lcp or 0,
            fid=pm.fid or 0,
            cls=pm.cls or 0,
            ttfb=pm.ttfb or 0,
            speed_index=pm.speed_index or 0,
            total_blocking_time=pm.total_blocking_time or 0,
            first_contentful_paint=pm.first_contentful_paint or 0
        )

    seo_metrics = None
    if audit.seo_metrics:
        sm = audit.seo_metrics
        seo_metrics = SEOMetrics(
            score=sm.score,
            title=sm.title,
            title_length=sm.title_length,
            meta_description=sm.meta_description,
            meta_description_length=sm.meta_description_length,
            h1_count=sm.h1_count,
            h1_texts=sm.h1_texts or [],
            canonical_url=sm.canonical_url,
            robots_txt_exists=sm.robots_txt_exists,
            sitemap_exists=sm.sitemap_exists,
            structured_data=sm.structured_data or [],
            broken_links=sm.broken_links or [],
            image_alt_missing=sm.image_alt_missing
        )

    security_metrics = None
    if audit.security_metrics:
        secm = audit.security_metrics
        security_metrics = SecurityMetrics(
            score=secm.score,
            https_enabled=secm.https_enabled,
            ssl_valid=secm.ssl_valid,
            ssl_expiry_days=secm.ssl_expiry_days,
            hsts_enabled=secm.hsts_enabled,
            csp_enabled=secm.csp_enabled,
            x_frame_options=secm.x_frame_options,
            x_content_type_options=secm.x_content_type_options,
            cookies_secure=secm.cookies_secure,
            cookies_httponly=secm.cookies_httponly,
            exposed_emails=secm.exposed_emails or [],
            exposed_api_keys=secm.exposed_api_keys
        )

    gdpr_metrics = None
    if audit.gdpr_metrics:
        gm = audit.gdpr_metrics
        gdpr_metrics = GDPRMetrics(
            score=gm.score,
            cookie_banner_present=gm.cookie_banner_present,
            privacy_policy_link=gm.privacy_policy_link,
            cookie_categories_explained=gm.cookie_categories_explained,
            opt_out_option=gm.opt_out_option,
            third_party_trackers=gm.third_party_trackers or [],
            google_analytics=gm.google_analytics,
            facebook_pixel=gm.facebook_pixel,
            data_retention_info=gm.data_retention_info
        )

    accessibility_metrics = None
    if audit.accessibility_metrics:
        am = audit.accessibility_metrics
        accessibility_metrics = AccessibilityMetrics(
            score=am.score,
            wcag_level=am.wcag_level,
            color_contrast_issues=am.color_contrast_issues,
            missing_alt_texts=am.missing_alt_texts,
            missing_form_labels=am.missing_form_labels,
            keyboard_navigation=am.keyboard_navigation,
            aria_usage=am.aria_usage,
            heading_hierarchy_valid=am.heading_hierarchy_valid
        )

    return AuditResult(
        id=audit.id,
        url=audit.url,
        status=AuditStatus(audit.status),
        created_at=audit.created_at,
        completed_at=audit.completed_at,
        overall_score=audit.overall_score,
        performance_score=audit.performance_score,
        seo_score=audit.seo_score,
        security_score=audit.security_score,
        gdpr_score=audit.gdpr_score,
        accessibility_score=audit.accessibility_score,
        mobile_ux_score=getattr(audit, 'mobile_ux_score', None),
        trust_score=getattr(audit, 'trust_score', None),
        competitor_score=getattr(audit, 'competitor_score', None),
        performance=performance_metrics,
        seo=seo_metrics,
        security=security_metrics,
        gdpr=gdpr_metrics,
        accessibility=accessibility_metrics,
        issues=issues,
        desktop_screenshot=audit.desktop_screenshot,
        mobile_screenshot=audit.mobile_screenshot
    )


@app.get("/api/audit/{audit_id}/pdf")
async def download_audit_pdf(
    audit_id: str,
    lang: str = Query("ro", description="Language: 'ro' or 'en'"),
    db: AsyncSession = Depends(get_db)
):
    """Download audit report as PDF"""
    audit_repo = AuditRepository(db)
    audit = await audit_repo.get_by_id(audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found" if lang == "en" else "Audit negasit")

    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Audit not completed" if lang == "en" else "Auditul nu este finalizat")

    # Generate PDF
    from reports.generator import generate_pdf_report

    # Convert to AuditResult for PDF generator
    audit_result = await get_audit(audit_id, db)
    pdf_path = await generate_pdf_report(audit_result, lang)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"audit_report_{audit_id[:8]}.pdf"
    )


@app.get("/api/audits")
async def list_audits(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    url_search: Optional[str] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's audits with filtering"""
    audit_repo = AuditRepository(db)

    result = await audit_repo.get_user_audits(
        user_id=current_user.id,
        page=page,
        limit=limit,
        status=status,
        url_search=url_search,
        min_score=min_score
    )

    # Convert audits to response format
    audits = []
    for audit in result["audits"]:
        audits.append({
            "id": audit.id,
            "url": audit.url,
            "status": audit.status,
            "overall_score": audit.overall_score,
            "performance_score": audit.performance_score,
            "seo_score": audit.seo_score,
            "security_score": audit.security_score,
            "gdpr_score": audit.gdpr_score,
            "accessibility_score": audit.accessibility_score,
            "mobile_ux_score": getattr(audit, 'mobile_ux_score', None),
            "trust_score": getattr(audit, 'trust_score', None),
            "competitor_score": getattr(audit, 'competitor_score', None),
            "issues_count": len(audit.issues),
            "created_at": audit.created_at.isoformat(),
            "completed_at": audit.completed_at.isoformat() if audit.completed_at else None
        })

    return {
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
        "pages": result["pages"],
        "audits": audits
    }


@app.delete("/api/audit/{audit_id}")
async def delete_audit(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an audit"""
    audit_repo = AuditRepository(db)
    audit = await audit_repo.get_by_id(audit_id, include_relations=False)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit negasit")

    # Check ownership
    if audit.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Nu aveti permisiunea de a sterge acest audit")

    await audit_repo.delete(audit_id)
    return {"message": "Audit sters cu succes"}


@app.post("/api/audit/{audit_id}/rerun", response_model=AuditResponse)
async def rerun_audit(
    audit_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Re-run an existing audit"""
    audit_repo = AuditRepository(db)
    old_audit = await audit_repo.get_by_id(audit_id, include_relations=False)

    if not old_audit:
        raise HTTPException(status_code=404, detail="Audit negasit")

    # Check credits
    if current_user.credits <= 0:
        raise HTTPException(
            status_code=402,
            detail="Credite insuficiente"
        )

    # Deduct credit
    user_repo = UserRepository(db)
    await user_repo.deduct_credit(current_user.id)

    # Create new audit
    audit = await audit_repo.create(
        url=old_audit.url,
        audit_types=old_audit.audit_types or ["full"],
        user_id=current_user.id
    )

    # Start audit in background
    background_tasks.add_task(
        run_audit,
        audit.id,
        old_audit.url,
        old_audit.audit_types or ["full"],
        True,  # include_screenshots
        True,  # mobile_test
        "ro"   # lang
    )

    return AuditResponse(
        success=True,
        audit_id=audit.id,
        message="Audit restarted successfully",
        status=AuditStatus.PENDING
    )


# ============== ESTIMATE ENDPOINTS ==============

@app.post("/api/estimate", response_model=PriceEstimate)
async def get_price_estimate(
    request: EstimateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get price estimate for fixing issues"""
    audit_repo = AuditRepository(db)
    audit = await audit_repo.get_by_id(request.audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit negasit")

    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Auditul nu este finalizat")

    from ai.analyzer import generate_price_estimate

    # Convert to AuditResult for estimator
    audit_result = await get_audit(request.audit_id, db)
    estimate = await generate_price_estimate(
        audit_result,
        request.hourly_rate,
        request.currency
    )

    return estimate


# ============== API TESTING ENDPOINTS ==============

@app.post("/api/test-api")
async def test_api_endpoints(
    request: APITestRequest,
    background_tasks: BackgroundTasks
):
    """Test API endpoints"""
    import uuid
    test_id = str(uuid.uuid4())

    background_tasks.add_task(
        run_api_tests,
        test_id,
        str(request.base_url),
        request.endpoints,
        request.auth_token
    )

    return {
        "test_id": test_id,
        "message": "API testing started",
        "status": "running"
    }


# ============== BACKGROUND TASKS ==============

async def run_audit(
    audit_id: str,
    url: str,
    audit_types: list,
    include_screenshots: bool,
    mobile_test: bool,
    lang: str = "ro"
):
    """Run the actual audit in background"""
    from database.connection import async_session

    async with async_session() as db:
        try:
            audit_repo = AuditRepository(db)

            # Update status to running
            await audit_repo.update_status(audit_id, "running")
            await db.commit()

            # Import auditors
            from auditors.performance import PerformanceAuditor
            from auditors.seo import SEOAuditor
            from auditors.security import SecurityAuditor
            from auditors.gdpr import GDPRAuditor
            from auditors.accessibility import AccessibilityAuditor

            issues = []
            scores = {}

            # Run selected audits
            if "full" in audit_types or "performance" in audit_types:
                perf_auditor = PerformanceAuditor()
                perf_result = await perf_auditor.audit(url, mobile_test, lang)
                scores["performance"] = perf_result.score

                # Save metrics
                await audit_repo.add_performance_metrics(audit_id, {
                    "score": perf_result.score,
                    "lcp": getattr(perf_result.metrics, 'lcp', None),
                    "fid": getattr(perf_result.metrics, 'fid', None),
                    "cls": getattr(perf_result.metrics, 'cls', None),
                    "ttfb": getattr(perf_result.metrics, 'ttfb', None),
                    "speed_index": getattr(perf_result.metrics, 'speed_index', None),
                    "total_blocking_time": getattr(perf_result.metrics, 'total_blocking_time', None),
                    "first_contentful_paint": getattr(perf_result.metrics, 'first_contentful_paint', None)
                })

                for issue in perf_result.issues:
                    issues.append({
                        "category": "performance",
                        "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                        "title": issue.title,
                        "description": issue.description,
                        "recommendation": issue.recommendation,
                        "affected_element": getattr(issue, 'affected_element', None),
                        "estimated_hours": getattr(issue, 'estimated_hours', 1.0),
                        "complexity": getattr(issue, 'complexity', 'medium')
                    })

            if "full" in audit_types or "seo" in audit_types:
                seo_auditor = SEOAuditor()
                seo_result = await seo_auditor.audit(url, lang)
                scores["seo"] = seo_result.score
                scores["tseo"] = seo_result.tseo_score
                scores["opseo"] = seo_result.opseo_score

                await audit_repo.add_seo_metrics(audit_id, {
                    "score": seo_result.score,
                    "title": getattr(seo_result.metrics, 'title', None),
                    "title_length": getattr(seo_result.metrics, 'title_length', 0),
                    "meta_description": getattr(seo_result.metrics, 'meta_description', None),
                    "meta_description_length": getattr(seo_result.metrics, 'meta_description_length', 0),
                    "h1_count": getattr(seo_result.metrics, 'h1_count', 0),
                    "h1_texts": getattr(seo_result.metrics, 'h1_texts', []),
                    "canonical_url": getattr(seo_result.metrics, 'canonical_url', None),
                    "robots_txt_exists": getattr(seo_result.metrics, 'robots_txt_exists', False),
                    "sitemap_exists": getattr(seo_result.metrics, 'sitemap_exists', False),
                    "structured_data": getattr(seo_result.metrics, 'structured_data', []),
                    "broken_links": getattr(seo_result.metrics, 'broken_links', []),
                    "image_alt_missing": getattr(seo_result.metrics, 'image_alt_missing', 0)
                })

                for issue in seo_result.issues:
                    issues.append({
                        "category": "seo",
                        "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                        "title": issue.title,
                        "description": issue.description,
                        "recommendation": issue.recommendation,
                        "affected_element": getattr(issue, 'affected_element', None),
                        "estimated_hours": getattr(issue, 'estimated_hours', 1.0),
                        "complexity": getattr(issue, 'complexity', 'medium')
                    })

            if "full" in audit_types or "security" in audit_types:
                sec_auditor = SecurityAuditor()
                sec_result = await sec_auditor.audit(url, lang)
                scores["security"] = sec_result.score

                await audit_repo.add_security_metrics(audit_id, {
                    "score": sec_result.score,
                    "https_enabled": getattr(sec_result.metrics, 'https_enabled', False),
                    "ssl_valid": getattr(sec_result.metrics, 'ssl_valid', False),
                    "ssl_expiry_days": getattr(sec_result.metrics, 'ssl_expiry_days', None),
                    "hsts_enabled": getattr(sec_result.metrics, 'hsts_enabled', False),
                    "csp_enabled": getattr(sec_result.metrics, 'csp_enabled', False),
                    "x_frame_options": getattr(sec_result.metrics, 'x_frame_options', False),
                    "x_content_type_options": getattr(sec_result.metrics, 'x_content_type_options', False),
                    "cookies_secure": getattr(sec_result.metrics, 'cookies_secure', False),
                    "cookies_httponly": getattr(sec_result.metrics, 'cookies_httponly', False),
                    "exposed_emails": getattr(sec_result.metrics, 'exposed_emails', []),
                    "exposed_api_keys": getattr(sec_result.metrics, 'exposed_api_keys', False)
                })

                for issue in sec_result.issues:
                    issues.append({
                        "category": "security",
                        "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                        "title": issue.title,
                        "description": issue.description,
                        "recommendation": issue.recommendation,
                        "affected_element": getattr(issue, 'affected_element', None),
                        "estimated_hours": getattr(issue, 'estimated_hours', 1.0),
                        "complexity": getattr(issue, 'complexity', 'medium')
                    })

            if "full" in audit_types or "gdpr" in audit_types:
                gdpr_auditor = GDPRAuditor()
                gdpr_result = await gdpr_auditor.audit(url, lang)
                scores["gdpr"] = gdpr_result.score

                await audit_repo.add_gdpr_metrics(audit_id, {
                    "score": gdpr_result.score,
                    "cookie_banner_present": getattr(gdpr_result.metrics, 'cookie_banner_present', False),
                    "privacy_policy_link": getattr(gdpr_result.metrics, 'privacy_policy_link', False),
                    "cookie_categories_explained": getattr(gdpr_result.metrics, 'cookie_categories_explained', False),
                    "opt_out_option": getattr(gdpr_result.metrics, 'opt_out_option', False),
                    "third_party_trackers": getattr(gdpr_result.metrics, 'third_party_trackers', []),
                    "google_analytics": getattr(gdpr_result.metrics, 'google_analytics', False),
                    "facebook_pixel": getattr(gdpr_result.metrics, 'facebook_pixel', False),
                    "data_retention_info": getattr(gdpr_result.metrics, 'data_retention_info', False)
                })

                for issue in gdpr_result.issues:
                    issues.append({
                        "category": "gdpr",
                        "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                        "title": issue.title,
                        "description": issue.description,
                        "recommendation": issue.recommendation,
                        "affected_element": getattr(issue, 'affected_element', None),
                        "estimated_hours": getattr(issue, 'estimated_hours', 1.0),
                        "complexity": getattr(issue, 'complexity', 'medium')
                    })

            if "full" in audit_types or "accessibility" in audit_types:
                a11y_auditor = AccessibilityAuditor()
                a11y_result = await a11y_auditor.audit(url, lang)
                scores["accessibility"] = a11y_result.score

                await audit_repo.add_accessibility_metrics(audit_id, {
                    "score": a11y_result.score,
                    "wcag_level": getattr(a11y_result.metrics, 'wcag_level', "A"),
                    "color_contrast_issues": getattr(a11y_result.metrics, 'color_contrast_issues', 0),
                    "missing_alt_texts": getattr(a11y_result.metrics, 'missing_alt_texts', 0),
                    "missing_form_labels": getattr(a11y_result.metrics, 'missing_form_labels', 0),
                    "keyboard_navigation": getattr(a11y_result.metrics, 'keyboard_navigation', False),
                    "aria_usage": getattr(a11y_result.metrics, 'aria_usage', 0),
                    "heading_hierarchy_valid": getattr(a11y_result.metrics, 'heading_hierarchy_valid', False)
                })

                for issue in a11y_result.issues:
                    issues.append({
                        "category": "accessibility",
                        "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                        "title": issue.title,
                        "description": issue.description,
                        "recommendation": issue.recommendation,
                        "affected_element": getattr(issue, 'affected_element', None),
                        "estimated_hours": getattr(issue, 'estimated_hours', 1.0),
                        "complexity": getattr(issue, 'complexity', 'medium')
                    })

            # ── New v1 auditors: MOBUX, TRUST, COMP ──────────────────
            if "full" in audit_types:
                from auditors.mobile_ux import MobileUXAuditor
                from auditors.trust import TrustAuditor
                from auditors.competitor import CompetitorAuditor

                # Mobile UX
                try:
                    mobux_auditor = MobileUXAuditor()
                    mobux_result = await mobux_auditor.audit(url, lang)
                    scores["mobile_ux"] = mobux_result.score
                    for issue in mobux_result.issues:
                        issues.append({
                            "category": "ui_ux",
                            "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                            "title": issue.title,
                            "description": issue.description,
                            "recommendation": issue.recommendation,
                            "affected_element": getattr(issue, 'affected_element', None),
                            "estimated_hours": getattr(issue, 'estimated_hours', 1.0),
                            "complexity": getattr(issue, 'complexity', 'medium')
                        })
                except Exception as e:
                    print(f"Mobile UX audit error: {e}")

                # Trust & Conversions
                try:
                    trust_auditor = TrustAuditor()
                    trust_result = await trust_auditor.audit(url, lang)
                    scores["trust"] = trust_result.score
                    for issue in trust_result.issues:
                        issues.append({
                            "category": "ui_ux",
                            "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                            "title": issue.title,
                            "description": issue.description,
                            "recommendation": issue.recommendation,
                            "affected_element": getattr(issue, 'affected_element', None),
                            "estimated_hours": getattr(issue, 'estimated_hours', 1.0),
                            "complexity": getattr(issue, 'complexity', 'medium')
                        })
                except Exception as e:
                    print(f"Trust audit error: {e}")

                # Competitor Gap (no competitor URL in v1 basic flow)
                try:
                    comp_auditor = CompetitorAuditor()
                    comp_result = await comp_auditor.audit(url, competitor_url=None, lang=lang)
                    scores["competitor"] = comp_result.score
                    for issue in comp_result.issues:
                        issues.append({
                            "category": "full",
                            "severity": issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                            "title": issue.title,
                            "description": issue.description,
                            "recommendation": issue.recommendation,
                            "affected_element": getattr(issue, 'affected_element', None),
                            "estimated_hours": getattr(issue, 'estimated_hours', 0),
                            "complexity": getattr(issue, 'complexity', 'simple')
                        })
                except Exception as e:
                    print(f"Competitor audit error: {e}")

            # Add all issues to database
            if issues:
                await audit_repo.add_issues_bulk(audit_id, issues)

            # Calculate overall score using weighted scoring engine
            from services.scoring import from_legacy_scores, compute_overall_score
            comp_scores = from_legacy_scores(
                performance_score=scores.get("performance"),
                seo_score=scores.get("seo"),
                security_score=scores.get("security"),
                gdpr_score=scores.get("gdpr"),
                accessibility_score=scores.get("accessibility"),
                mobile_ux_score=scores.get("mobile_ux"),
                trust_score=scores.get("trust"),
                competitor_score=scores.get("competitor"),
                tseo_score=scores.get("tseo"),
                opseo_score=scores.get("opseo"),
            )
            overall_result = compute_overall_score(comp_scores)
            overall_score = overall_result.overall_score

            # Update scores
            await audit_repo.update_scores(
                audit_id,
                overall_score=overall_score,
                performance_score=scores.get("performance"),
                seo_score=scores.get("seo"),
                security_score=scores.get("security"),
                gdpr_score=scores.get("gdpr"),
                accessibility_score=scores.get("accessibility"),
                mobile_ux_score=scores.get("mobile_ux"),
                trust_score=scores.get("trust"),
                competitor_score=scores.get("competitor"),
            )

            # Take screenshots if requested
            if include_screenshots:
                try:
                    from auditors.screenshots import take_screenshots
                    screenshots = await take_screenshots(url, mobile_test)
                    await audit_repo.update_screenshots(
                        audit_id,
                        desktop=screenshots.get('desktop'),
                        mobile=screenshots.get('mobile')
                    )
                except Exception as e:
                    print(f"Screenshot error: {e}")

            # Mark as completed
            await audit_repo.update_status(audit_id, "completed", datetime.utcnow())
            await db.commit()

            # Send "preview ready" email (non-blocking)
            try:
                from services.email_service import send_preview_ready, send_admin_new_audit
                # Find email from audit logs
                from database.models import AuditLog
                from sqlalchemy import select as sel
                log_result = await db.execute(
                    sel(AuditLog.email)
                    .where(AuditLog.entity_id == audit_id, AuditLog.email.isnot(None))
                    .limit(1)
                )
                lead_email = log_result.scalar_one_or_none()
                if lead_email:
                    send_preview_ready(lead_email, url, audit_id, overall_score)
                send_admin_new_audit(url, audit_id, lead_email)
            except Exception as e:
                print(f"Email notification error: {e}")

        except Exception as e:
            await audit_repo.update_status(audit_id, "failed")
            await db.commit()
            print(f"Audit failed: {e}")
            import traceback
            traceback.print_exc()


async def run_api_tests(test_id: str, base_url: str, endpoints: list, auth_token: str):
    """Run API endpoint tests"""
    from auditors.api_tester import APITester

    tester = APITester(base_url, auth_token)
    results = await tester.test_endpoints(endpoints)
    return results


# ============== MAIN ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
