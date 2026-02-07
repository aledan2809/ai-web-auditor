"""
Competitor Monitoring API Endpoints
Track and compare competitor website performance
"""

from typing import List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from database.connection import get_db
from database.models import Competitor, CompetitorAudit, Audit, User
from auth.dependencies import get_current_user


router = APIRouter(prefix="/api/competitors", tags=["competitors"])


# ============== SCHEMAS ==============

class AddCompetitorRequest(BaseModel):
    name: str
    url: str
    monitor_frequency: str = "weekly"  # daily, weekly, monthly


class CompetitorResponse(BaseModel):
    id: str
    name: str
    url: str
    domain: str
    is_active: bool
    monitor_frequency: str
    latest_overall_score: Optional[int]
    latest_performance_score: Optional[int]
    latest_seo_score: Optional[int]
    latest_security_score: Optional[int]
    latest_gdpr_score: Optional[int]
    latest_accessibility_score: Optional[int]
    score_change: int
    last_audit_at: Optional[str]
    created_at: str


class CompetitorAuditResponse(BaseModel):
    id: str
    overall_score: int
    performance_score: Optional[int]
    seo_score: Optional[int]
    security_score: Optional[int]
    gdpr_score: Optional[int]
    accessibility_score: Optional[int]
    score_change: int
    created_at: str


class ComparisonData(BaseModel):
    my_url: str
    my_scores: dict
    competitors: List[dict]


class UpdateCompetitorRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    monitor_frequency: Optional[str] = None


# ============== HELPER FUNCTIONS ==============

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace("www.", "")
        return domain.lower()
    except:
        return url


async def run_competitor_audit(competitor_id: str, db: AsyncSession):
    """Background task to run audit for a competitor"""
    # This would trigger the actual audit process
    # For now, we'll just mark it as needing audit
    pass


# ============== ENDPOINTS ==============

@router.get("", response_model=List[CompetitorResponse])
async def get_competitors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all competitors for current user"""
    result = await db.execute(
        select(Competitor)
        .where(Competitor.user_id == current_user.id)
        .order_by(Competitor.created_at.desc())
    )
    competitors = result.scalars().all()

    return [
        CompetitorResponse(
            id=c.id,
            name=c.name,
            url=c.url,
            domain=c.domain,
            is_active=c.is_active,
            monitor_frequency=c.monitor_frequency,
            latest_overall_score=c.latest_overall_score,
            latest_performance_score=c.latest_performance_score,
            latest_seo_score=c.latest_seo_score,
            latest_security_score=c.latest_security_score,
            latest_gdpr_score=c.latest_gdpr_score,
            latest_accessibility_score=c.latest_accessibility_score,
            score_change=c.score_change or 0,
            last_audit_at=c.last_audit_at.isoformat() if c.last_audit_at else None,
            created_at=c.created_at.isoformat()
        )
        for c in competitors
    ]


@router.post("", response_model=CompetitorResponse)
async def add_competitor(
    request: AddCompetitorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new competitor to monitor"""
    # Validate URL
    url = request.url
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    domain = extract_domain(url)

    # Check if competitor already exists for this user
    existing = await db.execute(
        select(Competitor).where(
            and_(
                Competitor.user_id == current_user.id,
                Competitor.domain == domain
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competitor with this domain already exists"
        )

    # Check competitor limit (e.g., 5 for free users, 20 for premium)
    count_result = await db.execute(
        select(func.count(Competitor.id)).where(
            Competitor.user_id == current_user.id
        )
    )
    competitor_count = count_result.scalar()

    max_competitors = 20 if current_user.credits > 0 else 5
    if competitor_count >= max_competitors:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum {max_competitors} competitors allowed"
        )

    # Create competitor
    competitor = Competitor(
        user_id=current_user.id,
        name=request.name,
        url=url,
        domain=domain,
        monitor_frequency=request.monitor_frequency
    )
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)

    return CompetitorResponse(
        id=competitor.id,
        name=competitor.name,
        url=competitor.url,
        domain=competitor.domain,
        is_active=competitor.is_active,
        monitor_frequency=competitor.monitor_frequency,
        latest_overall_score=None,
        latest_performance_score=None,
        latest_seo_score=None,
        latest_security_score=None,
        latest_gdpr_score=None,
        latest_accessibility_score=None,
        score_change=0,
        last_audit_at=None,
        created_at=competitor.created_at.isoformat()
    )


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific competitor"""
    result = await db.execute(
        select(Competitor).where(
            and_(
                Competitor.id == competitor_id,
                Competitor.user_id == current_user.id
            )
        )
    )
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    return CompetitorResponse(
        id=competitor.id,
        name=competitor.name,
        url=competitor.url,
        domain=competitor.domain,
        is_active=competitor.is_active,
        monitor_frequency=competitor.monitor_frequency,
        latest_overall_score=competitor.latest_overall_score,
        latest_performance_score=competitor.latest_performance_score,
        latest_seo_score=competitor.latest_seo_score,
        latest_security_score=competitor.latest_security_score,
        latest_gdpr_score=competitor.latest_gdpr_score,
        latest_accessibility_score=competitor.latest_accessibility_score,
        score_change=competitor.score_change or 0,
        last_audit_at=competitor.last_audit_at.isoformat() if competitor.last_audit_at else None,
        created_at=competitor.created_at.isoformat()
    )


@router.patch("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: str,
    request: UpdateCompetitorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a competitor"""
    result = await db.execute(
        select(Competitor).where(
            and_(
                Competitor.id == competitor_id,
                Competitor.user_id == current_user.id
            )
        )
    )
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    if request.name is not None:
        competitor.name = request.name
    if request.is_active is not None:
        competitor.is_active = request.is_active
    if request.monitor_frequency is not None:
        competitor.monitor_frequency = request.monitor_frequency

    competitor.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(competitor)

    return CompetitorResponse(
        id=competitor.id,
        name=competitor.name,
        url=competitor.url,
        domain=competitor.domain,
        is_active=competitor.is_active,
        monitor_frequency=competitor.monitor_frequency,
        latest_overall_score=competitor.latest_overall_score,
        latest_performance_score=competitor.latest_performance_score,
        latest_seo_score=competitor.latest_seo_score,
        latest_security_score=competitor.latest_security_score,
        latest_gdpr_score=competitor.latest_gdpr_score,
        latest_accessibility_score=competitor.latest_accessibility_score,
        score_change=competitor.score_change or 0,
        last_audit_at=competitor.last_audit_at.isoformat() if competitor.last_audit_at else None,
        created_at=competitor.created_at.isoformat()
    )


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a competitor"""
    result = await db.execute(
        select(Competitor).where(
            and_(
                Competitor.id == competitor_id,
                Competitor.user_id == current_user.id
            )
        )
    )
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    await db.delete(competitor)
    await db.commit()

    return {"success": True, "message": "Competitor deleted"}


@router.get("/{competitor_id}/history", response_model=List[CompetitorAuditResponse])
async def get_competitor_history(
    competitor_id: str,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit history for a competitor"""
    # Verify ownership
    result = await db.execute(
        select(Competitor).where(
            and_(
                Competitor.id == competitor_id,
                Competitor.user_id == current_user.id
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    # Get history
    result = await db.execute(
        select(CompetitorAudit)
        .where(CompetitorAudit.competitor_id == competitor_id)
        .order_by(CompetitorAudit.created_at.desc())
        .limit(limit)
    )
    audits = result.scalars().all()

    return [
        CompetitorAuditResponse(
            id=a.id,
            overall_score=a.overall_score,
            performance_score=a.performance_score,
            seo_score=a.seo_score,
            security_score=a.security_score,
            gdpr_score=a.gdpr_score,
            accessibility_score=a.accessibility_score,
            score_change=a.score_change or 0,
            created_at=a.created_at.isoformat()
        )
        for a in audits
    ]


@router.post("/{competitor_id}/audit")
async def trigger_competitor_audit(
    competitor_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger an audit for a competitor"""
    result = await db.execute(
        select(Competitor).where(
            and_(
                Competitor.id == competitor_id,
                Competitor.user_id == current_user.id
            )
        )
    )
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found"
        )

    # Check if user has credits
    if current_user.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits"
        )

    # Deduct credit
    current_user.credits -= 1

    # Start audit (in production, this would call the audit engine)
    # For now, we'll create a placeholder response
    from models.schemas import AuditRequest

    # Import here to avoid circular imports
    from main import start_audit_background

    audit_request = AuditRequest(
        url=competitor.url,
        audit_types=["full"],
        include_screenshots=True,
        mobile_test=True
    )

    # Create audit record
    audit = Audit(
        user_id=current_user.id,
        url=competitor.url,
        status="pending",
        audit_types=["full"]
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    # Schedule background audit
    background_tasks.add_task(
        start_audit_background,
        audit.id,
        audit_request
    )

    return {
        "success": True,
        "audit_id": audit.id,
        "message": "Audit started for competitor"
    }


@router.get("/compare/all", response_model=ComparisonData)
async def compare_with_competitors(
    my_audit_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare your website with all competitors"""
    # Get user's latest audit or specified audit
    if my_audit_id:
        result = await db.execute(
            select(Audit).where(
                and_(
                    Audit.id == my_audit_id,
                    Audit.user_id == current_user.id
                )
            )
        )
    else:
        result = await db.execute(
            select(Audit)
            .where(
                and_(
                    Audit.user_id == current_user.id,
                    Audit.status == "completed"
                )
            )
            .order_by(Audit.created_at.desc())
            .limit(1)
        )

    my_audit = result.scalar_one_or_none()

    if not my_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed audit found"
        )

    # Get all competitors with their latest scores
    result = await db.execute(
        select(Competitor)
        .where(
            and_(
                Competitor.user_id == current_user.id,
                Competitor.is_active == True,
                Competitor.latest_overall_score.isnot(None)
            )
        )
        .order_by(Competitor.latest_overall_score.desc())
    )
    competitors = result.scalars().all()

    return ComparisonData(
        my_url=my_audit.url,
        my_scores={
            "overall": my_audit.overall_score,
            "performance": my_audit.performance_score,
            "seo": my_audit.seo_score,
            "security": my_audit.security_score,
            "gdpr": my_audit.gdpr_score,
            "accessibility": my_audit.accessibility_score
        },
        competitors=[
            {
                "id": c.id,
                "name": c.name,
                "url": c.url,
                "domain": c.domain,
                "scores": {
                    "overall": c.latest_overall_score,
                    "performance": c.latest_performance_score,
                    "seo": c.latest_seo_score,
                    "security": c.latest_security_score,
                    "gdpr": c.latest_gdpr_score,
                    "accessibility": c.latest_accessibility_score
                },
                "score_change": c.score_change or 0,
                "last_audit_at": c.last_audit_at.isoformat() if c.last_audit_at else None
            }
            for c in competitors
        ]
    )
