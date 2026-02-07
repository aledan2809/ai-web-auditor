"""
Settings API Endpoints
Handles pricing, packages, and company settings
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional, List
import json

from database.connection import get_db
from database.models import Package, Settings, CompanyDetails
from auth.dependencies import require_admin
from pydantic import BaseModel


router = APIRouter(prefix="/api", tags=["settings"])


# ============== SCHEMAS ==============

class PackageConfig(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "EUR"
    audits_included: int
    total_audits: int = 6
    features: List[str]
    pdf_type: str = "none"
    popular: bool = False
    requires_share: bool = False
    is_active: bool = True


class CompanyDetailsSchema(BaseModel):
    name: str
    address: Optional[str] = None
    vat_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    swift: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class PricingSettings(BaseModel):
    packages: List[PackageConfig]
    hourly_rate: float = 75
    currency: str = "EUR"
    vat_rate: float = 0
    company_details: CompanyDetailsSchema


class UpdatePackageRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    audits_included: Optional[int] = None
    features: Optional[List[str]] = None
    pdf_type: Optional[str] = None
    popular: Optional[bool] = None
    requires_share: Optional[bool] = None
    is_active: Optional[bool] = None


# ============== DEFAULT DATA ==============

DEFAULT_PACKAGES = [
    {
        "id": "starter",
        "name": "Starter",
        "price": 0,
        "currency": "EUR",
        "audits_included": 2,
        "total_audits": 6,
        "features": ["Choose 2 audit types", "Basic score overview", "Share on social media"],
        "pdf_type": "none",
        "popular": False,
        "requires_share": True,
        "is_active": True,
        "sort_order": 1
    },
    {
        "id": "pro",
        "name": "Pro",
        "price": 1.99,
        "currency": "EUR",
        "audits_included": 4,
        "total_audits": 6,
        "features": ["Choose 4 audit types", "Detailed issue breakdown", "Basic PDF report", "Email delivery"],
        "pdf_type": "basic",
        "popular": True,
        "requires_share": False,
        "is_active": True,
        "sort_order": 2
    },
    {
        "id": "full",
        "name": "Full",
        "price": 4.99,
        "currency": "EUR",
        "audits_included": 6,
        "total_audits": 6,
        "features": ["All 6 audit types", "Full issue details", "Professional PDF report", "Priority support", "AI recommendations"],
        "pdf_type": "professional",
        "popular": False,
        "requires_share": False,
        "is_active": True,
        "sort_order": 3
    }
]

DEFAULT_COMPANY = {
    "name": "AI Web Auditor FZ-LLC",
    "address": "Dubai Silicon Oasis, Dubai, UAE",
    "vat_number": "",
    "bank_name": "Wio Business",
    "bank_account": "",
    "swift": "",
    "email": "support@aiwebauditor.com",
    "website": "https://aiwebauditor.com"
}


# ============== HELPER FUNCTIONS ==============

async def get_or_create_setting(db: AsyncSession, key: str, default_value: any) -> any:
    """Get a setting value or create with default"""
    result = await db.execute(
        select(Settings).where(Settings.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        return setting.value
    else:
        # Create with default
        new_setting = Settings(key=key, value=default_value)
        db.add(new_setting)
        await db.commit()
        return default_value


async def set_setting(db: AsyncSession, key: str, value: any):
    """Set a setting value"""
    result = await db.execute(
        select(Settings).where(Settings.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
    else:
        new_setting = Settings(key=key, value=value)
        db.add(new_setting)

    await db.commit()


async def ensure_default_packages(db: AsyncSession):
    """Ensure default packages exist"""
    for pkg_data in DEFAULT_PACKAGES:
        result = await db.execute(
            select(Package).where(Package.id == pkg_data["id"])
        )
        if not result.scalar_one_or_none():
            pkg = Package(**pkg_data)
            db.add(pkg)

    await db.commit()


async def ensure_company_details(db: AsyncSession):
    """Ensure company details exist"""
    result = await db.execute(select(CompanyDetails))
    if not result.scalar_one_or_none():
        company = CompanyDetails(**DEFAULT_COMPANY)
        db.add(company)
        await db.commit()


# ============== PUBLIC ENDPOINTS ==============

@router.get("/packages", response_model=List[PackageConfig])
async def get_packages(
    db: AsyncSession = Depends(get_db)
):
    """Get all active packages (public)"""
    await ensure_default_packages(db)

    result = await db.execute(
        select(Package)
        .where(Package.is_active == True)
        .order_by(Package.sort_order)
    )
    packages = result.scalars().all()

    return [
        PackageConfig(
            id=pkg.id,
            name=pkg.name,
            price=pkg.price,
            currency=pkg.currency,
            audits_included=pkg.audits_included,
            total_audits=pkg.total_audits,
            features=pkg.features or [],
            pdf_type=pkg.pdf_type,
            popular=pkg.popular,
            requires_share=pkg.requires_share,
            is_active=pkg.is_active
        )
        for pkg in packages
    ]


# ============== ADMIN ENDPOINTS ==============

@router.get("/admin/settings/pricing", response_model=PricingSettings)
async def get_pricing_settings(
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Get all pricing settings (admin only)"""
    await ensure_default_packages(db)
    await ensure_company_details(db)

    # Get packages
    packages_result = await db.execute(
        select(Package).order_by(Package.sort_order)
    )
    packages = packages_result.scalars().all()

    # Get settings
    hourly_rate = await get_or_create_setting(db, "hourly_rate", 75)
    currency = await get_or_create_setting(db, "currency", "EUR")
    vat_rate = await get_or_create_setting(db, "vat_rate", 0)

    # Get company details
    company_result = await db.execute(select(CompanyDetails))
    company = company_result.scalar_one_or_none()

    return PricingSettings(
        packages=[
            PackageConfig(
                id=pkg.id,
                name=pkg.name,
                price=pkg.price,
                currency=pkg.currency,
                audits_included=pkg.audits_included,
                total_audits=pkg.total_audits,
                features=pkg.features or [],
                pdf_type=pkg.pdf_type,
                popular=pkg.popular,
                requires_share=pkg.requires_share,
                is_active=pkg.is_active
            )
            for pkg in packages
        ],
        hourly_rate=hourly_rate,
        currency=currency,
        vat_rate=vat_rate,
        company_details=CompanyDetailsSchema(
            name=company.name if company else DEFAULT_COMPANY["name"],
            address=company.address if company else DEFAULT_COMPANY["address"],
            vat_number=company.vat_number if company else DEFAULT_COMPANY["vat_number"],
            bank_name=company.bank_name if company else DEFAULT_COMPANY["bank_name"],
            bank_account=company.bank_account if company else DEFAULT_COMPANY["bank_account"],
            swift=company.swift if company else DEFAULT_COMPANY["swift"],
            email=company.email if company else DEFAULT_COMPANY["email"],
            website=company.website if company else DEFAULT_COMPANY["website"]
        )
    )


@router.patch("/admin/settings/pricing")
async def update_pricing_settings(
    settings: PricingSettings,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Update pricing settings (admin only)"""
    # Update general settings
    await set_setting(db, "hourly_rate", settings.hourly_rate)
    await set_setting(db, "currency", settings.currency)
    await set_setting(db, "vat_rate", settings.vat_rate)

    # Update packages
    for pkg_data in settings.packages:
        result = await db.execute(
            select(Package).where(Package.id == pkg_data.id)
        )
        pkg = result.scalar_one_or_none()

        if pkg:
            pkg.name = pkg_data.name
            pkg.price = pkg_data.price
            pkg.currency = pkg_data.currency
            pkg.audits_included = pkg_data.audits_included
            pkg.total_audits = pkg_data.total_audits
            pkg.features = pkg_data.features
            pkg.pdf_type = pkg_data.pdf_type
            pkg.popular = pkg_data.popular
            pkg.requires_share = pkg_data.requires_share
            pkg.is_active = pkg_data.is_active
            pkg.updated_at = datetime.utcnow()
        else:
            new_pkg = Package(
                id=pkg_data.id,
                name=pkg_data.name,
                price=pkg_data.price,
                currency=pkg_data.currency,
                audits_included=pkg_data.audits_included,
                total_audits=pkg_data.total_audits,
                features=pkg_data.features,
                pdf_type=pkg_data.pdf_type,
                popular=pkg_data.popular,
                requires_share=pkg_data.requires_share,
                is_active=pkg_data.is_active
            )
            db.add(new_pkg)

    # Update company details
    company_result = await db.execute(select(CompanyDetails))
    company = company_result.scalar_one_or_none()

    if company:
        company.name = settings.company_details.name
        company.address = settings.company_details.address
        company.vat_number = settings.company_details.vat_number
        company.bank_name = settings.company_details.bank_name
        company.bank_account = settings.company_details.bank_account
        company.swift = settings.company_details.swift
        company.email = settings.company_details.email
        company.website = settings.company_details.website
        company.updated_at = datetime.utcnow()
    else:
        new_company = CompanyDetails(
            name=settings.company_details.name,
            address=settings.company_details.address,
            vat_number=settings.company_details.vat_number,
            bank_name=settings.company_details.bank_name,
            bank_account=settings.company_details.bank_account,
            swift=settings.company_details.swift,
            email=settings.company_details.email,
            website=settings.company_details.website
        )
        db.add(new_company)

    await db.commit()

    return {"success": True, "message": "Settings updated"}


@router.patch("/admin/settings/packages/{package_id}")
async def update_package(
    package_id: str,
    update: UpdatePackageRequest,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_admin)
):
    """Update a single package (admin only)"""
    result = await db.execute(
        select(Package).where(Package.id == package_id)
    )
    pkg = result.scalar_one_or_none()

    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    # Update fields if provided
    if update.name is not None:
        pkg.name = update.name
    if update.price is not None:
        pkg.price = update.price
    if update.currency is not None:
        pkg.currency = update.currency
    if update.audits_included is not None:
        pkg.audits_included = update.audits_included
    if update.features is not None:
        pkg.features = update.features
    if update.pdf_type is not None:
        pkg.pdf_type = update.pdf_type
    if update.popular is not None:
        pkg.popular = update.popular
    if update.requires_share is not None:
        pkg.requires_share = update.requires_share
    if update.is_active is not None:
        pkg.is_active = update.is_active

    pkg.updated_at = datetime.utcnow()
    await db.commit()

    return PackageConfig(
        id=pkg.id,
        name=pkg.name,
        price=pkg.price,
        currency=pkg.currency,
        audits_included=pkg.audits_included,
        total_audits=pkg.total_audits,
        features=pkg.features or [],
        pdf_type=pkg.pdf_type,
        popular=pkg.popular,
        requires_share=pkg.requires_share,
        is_active=pkg.is_active
    )
