"""
Stripe configuration and product definitions
"""

import os
import stripe
from pydantic_settings import BaseSettings


class StripeSettings(BaseSettings):
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_placeholder")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3001")

    class Config:
        env_file = ".env"


stripe_settings = StripeSettings()

# Initialize Stripe
stripe.api_key = stripe_settings.STRIPE_SECRET_KEY

# Product definitions (prices in EUR cents)
PRODUCTS = {
    "single": {
        "name": "Audit Unic",
        "price": 500,  # 5.00 EUR
        "credits": 1,
        "description": "1 audit de website",
        "mode": "payment"
    },
    "pack_5": {
        "name": "Pachet 5 Audituri",
        "price": 2000,  # 20.00 EUR
        "credits": 5,
        "description": "5 audituri (-20%)",
        "mode": "payment"
    },
    "pack_10": {
        "name": "Pachet 10 Audituri",
        "price": 3500,  # 35.00 EUR
        "credits": 10,
        "description": "10 audituri (-30%)",
        "mode": "payment"
    },
    "pack_20": {
        "name": "Pachet 20 Audituri",
        "price": 6000,  # 60.00 EUR
        "credits": 20,
        "description": "20 audituri (-40%)",
        "mode": "payment"
    },
    "monthly": {
        "name": "Abonament Lunar",
        "price": 2900,  # 29.00 EUR/luna
        "credits_per_month": 20,
        "description": "20 audituri/luna",
        "mode": "subscription",
        "interval": "month"
    },
    "yearly": {
        "name": "Abonament Anual",
        "price": 29000,  # 290.00 EUR/an
        "credits_per_month": 20,
        "description": "20 audituri/luna (2 luni gratuite)",
        "mode": "subscription",
        "interval": "year"
    }
}
