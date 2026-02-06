"""
Admin API routes
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.connection import get_db
from database.models import User, Audit, Payment, Subscription
from repositories.user_repo import UserRepository
from repositories.audit_repo import AuditRepository
from auth.dependencies import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ============== RESPONSE MODELS ==============

class UserStats(BaseModel):
    total: int
    new_this_month: int
    active: int


class AuditStats(BaseModel):
    total: int
    this_month: int
    avg_score: float
    by_status: dict


class RevenueStats(BaseModel):
    total: int  # cents
    this_month: int
    mrr: int  # Monthly Recurring Revenue


class TopIssue(BaseModel):
    title: str
    count: int


class DashboardStats(BaseModel):
    users: UserStats
    audits: AuditStats
    revenue: RevenueStats
    top_issues: List[TopIssue]


class AdminUserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    credits: int
    is_active: bool
    audits_count: int
    created_at: str


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    credits: Optional[int] = None
    is_active: Optional[bool] = None


# ============== ENDPOINTS ==============

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics"""

    # Calculate date ranges
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # User stats
    total_users = await db.execute(select(func.count(User.id)))
    total_users = total_users.scalar() or 0

    new_users = await db.execute(
        select(func.count(User.id))
        .where(User.created_at >= month_start)
    )
    new_users = new_users.scalar() or 0

    active_users = await db.execute(
        select(func.count(User.id))
        .where(User.is_active == True)
    )
    active_users = active_users.scalar() or 0

    # Audit stats
    audit_repo = AuditRepository(db)
    audit_stats = await audit_repo.get_stats()

    audits_this_month = await db.execute(
        select(func.count(Audit.id))
        .where(Audit.created_at >= month_start)
    )
    audits_this_month = audits_this_month.scalar() or 0

    # Revenue stats
    total_revenue = await db.execute(
        select(func.sum(Payment.amount))
        .where(Payment.status == "completed")
    )
    total_revenue = total_revenue.scalar() or 0

    revenue_this_month = await db.execute(
        select(func.sum(Payment.amount))
        .where(
            Payment.status == "completed",
            Payment.created_at >= month_start
        )
    )
    revenue_this_month = revenue_this_month.scalar() or 0

    # MRR from active subscriptions
    mrr = await db.execute(
        select(func.count(Subscription.id))
        .where(Subscription.status == "active")
    )
    active_subs = mrr.scalar() or 0
    mrr_value = active_subs * 2900  # 29 EUR per subscription

    return DashboardStats(
        users=UserStats(
            total=total_users,
            new_this_month=new_users,
            active=active_users
        ),
        audits=AuditStats(
            total=audit_stats["total"],
            this_month=audits_this_month,
            avg_score=audit_stats["avg_score"],
            by_status=audit_stats["by_status"]
        ),
        revenue=RevenueStats(
            total=total_revenue,
            this_month=revenue_this_month,
            mrr=mrr_value
        ),
        top_issues=[
            TopIssue(title=issue["title"], count=issue["count"])
            for issue in audit_stats["top_issues"]
        ]
    )


@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    query = select(User)

    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") |
            User.name.ilike(f"%{search}%")
        )

    if role:
        query = query.where(User.role == role)

    query = query.order_by(User.created_at.desc())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    # Get audit counts
    response = []
    for user in users:
        audit_count = await db.execute(
            select(func.count(Audit.id))
            .where(Audit.user_id == user.id)
        )
        audit_count = audit_count.scalar() or 0

        response.append(AdminUserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            credits=user.credits,
            is_active=user.is_active,
            audits_count=audit_count,
            created_at=user.created_at.isoformat()
        ))

    return response


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user details (admin only)"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizator negasit"
        )

    audit_count = await db.execute(
        select(func.count(Audit.id))
        .where(Audit.user_id == user.id)
    )
    audit_count = audit_count.scalar() or 0

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        credits=user.credits,
        is_active=user.is_active,
        audits_count=audit_count,
        created_at=user.created_at.isoformat()
    )


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    data: UpdateUserRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizator negasit"
        )

    # Prevent self-demotion
    if user.id == admin.id and data.role and data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nu va puteti modifica propriul rol"
        )

    # Update fields
    update_data = {}
    if data.role is not None:
        update_data["role"] = data.role
    if data.credits is not None:
        update_data["credits"] = data.credits
    if data.is_active is not None:
        update_data["is_active"] = data.is_active

    if update_data:
        user = await user_repo.update(user_id, **update_data)

    audit_count = await db.execute(
        select(func.count(Audit.id))
        .where(Audit.user_id == user.id)
    )
    audit_count = audit_count.scalar() or 0

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        credits=user.credits,
        is_active=user.is_active,
        audits_count=audit_count,
        created_at=user.created_at.isoformat()
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nu va puteti sterge propriul cont"
        )

    user_repo = UserRepository(db)
    success = await user_repo.delete(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizator negasit"
        )

    return {"message": "Utilizator sters cu succes"}


@router.get("/audits")
async def list_all_audits(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all audits (admin only)"""
    audit_repo = AuditRepository(db)
    result = await audit_repo.get_all(page=page, limit=limit, status=status)
    return result


@router.get("/payments")
async def list_all_payments(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all payments (admin only)"""
    query = select(Payment)

    if status:
        query = query.where(Payment.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    total = total.scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    payments = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "payments": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "product_type": p.product_type,
                "credits_added": p.credits_added,
                "created_at": p.created_at.isoformat()
            }
            for p in payments
        ]
    }
