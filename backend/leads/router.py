"""
Lead Capture API Endpoints
Handles enrollment, lead tracking, and conversion
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional, List
import uuid
import secrets

from database.connection import get_db
from database.models import Lead, Package, Audit, AuditLog
from auth.dependencies import get_current_user_optional, require_admin
from pydantic import BaseModel, EmailStr

# Marketing automation
from marketing.router import on_lead_created, on_lead_converted


router = APIRouter(prefix="/api/leads", tags=["leads"])


# ============== SCHEMAS ==============

class EnrollmentRequest(BaseModel):
    email: EmailStr
    name: str
    language: str = "en"
    audit_id: str
    package_id: str
    selected_audits: List[str] = []
    signature_data: Optional[str] = None
    newsletter_consent: bool = False
    fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    terms_hash: Optional[str] = None


class EnrollmentResponse(BaseModel):
    success: bool
    lead_id: str
    reference: str
    message: str


class LeadResponse(BaseModel):
    id: str
    reference: str
    email: str
    name: str
    language: str
    package_id: Optional[str]
    status: str
    payment_status: str
    created_at: datetime
    converted_at: Optional[datetime]


class VerifyEmailRequest(BaseModel):
    token: str


# ============== HELPER FUNCTIONS ==============

def generate_reference():
    """Generate unique lead reference: AWA-YYYYMMDD-XXXX"""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(2).upper()
    return f"AWA-{date_str}-{random_part}"


async def log_action(
    db: AsyncSession,
    action: str,
    entity_type: str = None,
    entity_id: str = None,
    email: str = None,
    ip_address: str = None,
    user_agent: str = None,
    details: dict = None
):
    """Log an action for audit trail"""
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {}
    )
    db.add(log)
    await db.commit()


# ============== ENDPOINTS ==============

@router.post("/enroll", response_model=EnrollmentResponse)
async def create_lead(
    request: EnrollmentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new lead from enrollment form.
    This is called after the user completes the enrollment form.
    """
    # Check if email already has a lead for this audit
    existing = await db.execute(
        select(Lead).where(
            Lead.email == request.email,
            Lead.audit_id == request.audit_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="You have already enrolled for this audit"
        )

    # Get audit to store URL
    audit_result = await db.execute(
        select(Audit).where(Audit.id == request.audit_id)
    )
    audit = audit_result.scalar_one_or_none()
    url = audit.url if audit else None

    # Generate reference
    reference = generate_reference()

    # Generate email verification token
    verification_token = secrets.token_urlsafe(32)

    # Create lead
    lead = Lead(
        reference=reference,
        email=request.email,
        name=request.name,
        language=request.language,
        audit_id=request.audit_id,
        url=url,
        package_id=request.package_id,
        selected_audits=request.selected_audits,
        signature_data=request.signature_data,
        newsletter_consent=request.newsletter_consent,
        fingerprint=request.fingerprint,
        ip_address=request.ip_address,
        user_agent=request.user_agent,
        terms_accepted_at=datetime.utcnow(),
        email_verification_token=verification_token,
        status="pending"
    )

    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    # Log the action
    await log_action(
        db,
        action="lead_created",
        entity_type="lead",
        entity_id=lead.id,
        email=request.email,
        ip_address=request.ip_address,
        user_agent=request.user_agent,
        details={
            "package_id": request.package_id,
            "audit_id": request.audit_id,
            "reference": reference
        }
    )

    # TODO: Send verification email in background
    # background_tasks.add_task(send_verification_email, lead.email, verification_token)

    # Trigger marketing automation webhooks
    background_tasks.add_task(on_lead_created, lead, db)

    return EnrollmentResponse(
        success=True,
        lead_id=lead.id,
        reference=reference,
        message="Enrollment successful"
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get lead status by ID"""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return LeadResponse(
        id=lead.id,
        reference=lead.reference,
        email=lead.email,
        name=lead.name,
        language=lead.language,
        package_id=lead.package_id,
        status=lead.status,
        payment_status=lead.payment_status,
        created_at=lead.created_at,
        converted_at=lead.converted_at
    )


@router.get("/reference/{reference}", response_model=LeadResponse)
async def get_lead_by_reference(
    reference: str,
    db: AsyncSession = Depends(get_db)
):
    """Get lead status by reference number"""
    result = await db.execute(
        select(Lead).where(Lead.reference == reference)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return LeadResponse(
        id=lead.id,
        reference=lead.reference,
        email=lead.email,
        name=lead.name,
        language=lead.language,
        package_id=lead.package_id,
        status=lead.status,
        payment_status=lead.payment_status,
        created_at=lead.created_at,
        converted_at=lead.converted_at
    )


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify lead email address"""
    result = await db.execute(
        select(Lead).where(Lead.email_verification_token == request.token)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    lead.email_verified = True
    lead.email_verification_token = None
    lead.status = "verified"

    await db.commit()

    await log_action(
        db,
        action="email_verified",
        entity_type="lead",
        entity_id=lead.id,
        email=lead.email
    )

    return {"success": True, "message": "Email verified successfully"}


@router.post("/{lead_id}/social-share")
async def complete_social_share(
    lead_id: str,
    platform: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Mark social share as completed (for free tier)"""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.package_id != "starter":
        raise HTTPException(status_code=400, detail="Social share only required for Starter package")

    lead.social_share_completed = True
    lead.social_share_platform = platform
    lead.status = "converted"
    lead.converted_at = datetime.utcnow()

    await db.commit()

    await log_action(
        db,
        action="social_share_completed",
        entity_type="lead",
        entity_id=lead.id,
        email=lead.email,
        details={"platform": platform}
    )

    # Trigger marketing automation webhooks
    background_tasks.add_task(on_lead_converted, lead, db)

    return {"success": True, "message": "Social share recorded"}


@router.patch("/{lead_id}/payment")
async def update_payment_status(
    lead_id: str,
    status: str,
    stripe_session_id: Optional[str] = None,
    invoice_number: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Update lead payment status (called by Stripe webhook)"""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.payment_status = status
    if stripe_session_id:
        lead.stripe_session_id = stripe_session_id
    if invoice_number:
        lead.invoice_number = invoice_number

    if status == "paid":
        lead.status = "converted"
        lead.converted_at = datetime.utcnow()

    await db.commit()

    await log_action(
        db,
        action="payment_status_updated",
        entity_type="lead",
        entity_id=lead.id,
        email=lead.email,
        details={
            "status": status,
            "stripe_session_id": stripe_session_id,
            "invoice_number": invoice_number
        }
    )

    return {"success": True}


# ============== ADMIN ENDPOINTS ==============

@router.get("/admin/list")
async def list_leads(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """List all leads (admin only)"""
    query = select(Lead)

    if status:
        query = query.where(Lead.status == status)

    query = query.order_by(Lead.created_at.desc())

    # Count total
    count_query = select(func.count(Lead.id))
    if status:
        count_query = count_query.where(Lead.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    leads = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "leads": [
            {
                "id": lead.id,
                "reference": lead.reference,
                "email": lead.email,
                "name": lead.name,
                "package_id": lead.package_id,
                "status": lead.status,
                "payment_status": lead.payment_status,
                "created_at": lead.created_at.isoformat(),
                "converted_at": lead.converted_at.isoformat() if lead.converted_at else None
            }
            for lead in leads
        ]
    }


@router.get("/admin/stats")
async def get_lead_stats(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Get lead statistics (admin only)"""
    # Total leads
    total_result = await db.execute(select(func.count(Lead.id)))
    total = total_result.scalar()

    # By status
    status_query = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    status_result = await db.execute(status_query)
    by_status = {row[0]: row[1] for row in status_result}

    # By package
    package_query = select(Lead.package_id, func.count(Lead.id)).group_by(Lead.package_id)
    package_result = await db.execute(package_query)
    by_package = {row[0] or "none": row[1] for row in package_result}

    # Conversion rate
    converted = by_status.get("converted", 0)
    conversion_rate = (converted / total * 100) if total > 0 else 0

    return {
        "total": total,
        "by_status": by_status,
        "by_package": by_package,
        "conversion_rate": round(conversion_rate, 2)
    }
