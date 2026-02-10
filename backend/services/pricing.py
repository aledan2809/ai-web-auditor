"""
AI Web Auditor — Pricing Service v1
Reference: DEV_DECISIONS_v1.md §4
"""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PricingConfig


# Default pricing (used when no DB row exists)
DEFAULT_PRICING = {
    "market": "UAE",
    "unlockPriceAED": 19.99,
    "quickWinsPriceAED": 199.0,
    "monitorMonthlyAED": 49.0,
    "normalUnlockPriceAED": 99.99,
    "normalFullPriceAED": 399.0,
    "isCampaign": False,
    "campaignPriceAED": None,
    "campaignEndsAt": None,
    "campaignLabel": None,
}


async def get_current_pricing(db: AsyncSession, market: str = "UAE") -> dict:
    """
    Get active pricing for a market.
    Returns API-ready dict matching API_CONTRACTS_AUDITOR_v1.md format.
    """
    result = await db.execute(
        select(PricingConfig)
        .where(PricingConfig.market == market, PricingConfig.is_active == True)
        .order_by(PricingConfig.updated_at.desc())
        .limit(1)
    )
    config = result.scalar_one_or_none()

    if not config:
        return DEFAULT_PRICING.copy()

    now = datetime.now(timezone.utc)
    is_campaign = (
        config.campaign_price is not None
        and config.campaign_ends_at is not None
        and config.campaign_ends_at > now
    )

    return {
        "market": config.market,
        "unlockPriceAED": config.campaign_price if is_campaign else config.unlock_price,
        "quickWinsPriceAED": config.quick_wins_price,
        "monitorMonthlyAED": config.monitor_monthly,
        "normalUnlockPriceAED": config.normal_unlock_price,
        "normalFullPriceAED": config.normal_full_price,
        "isCampaign": is_campaign,
        "campaignPriceAED": config.campaign_price if is_campaign else None,
        "campaignEndsAt": config.campaign_ends_at.isoformat() if is_campaign else None,
        "campaignLabel": config.campaign_label if is_campaign else None,
    }


async def seed_default_pricing(db: AsyncSession):
    """Insert default UAE pricing if none exists."""
    result = await db.execute(
        select(PricingConfig).where(PricingConfig.market == "UAE").limit(1)
    )
    if result.scalar_one_or_none() is None:
        config = PricingConfig(
            market="UAE",
            unlock_price=19.99,
            quick_wins_price=199.0,
            monitor_monthly=49.0,
            normal_unlock_price=99.99,
            normal_full_price=399.0,
            updated_by="system-seed",
        )
        db.add(config)
        await db.commit()
