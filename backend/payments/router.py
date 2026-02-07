"""
Payment API routes with Stripe integration
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe

from database.connection import get_db
from database.models import User, Payment, Subscription, Lead, Package
from repositories.user_repo import UserRepository
from auth.dependencies import get_current_user, get_current_user_optional
from .config import stripe_settings, PRODUCTS

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# ============== REQUEST/RESPONSE MODELS ==============

class CheckoutRequest(BaseModel):
    product_type: str


class LeadCheckoutRequest(BaseModel):
    lead_id: str
    package_id: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PaymentResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    product_type: Optional[str]
    credits_added: int
    created_at: str


class ProductResponse(BaseModel):
    id: str
    name: str
    price: int
    credits: Optional[int]
    credits_per_month: Optional[int]
    description: str
    mode: str


# ============== ENDPOINTS ==============

@router.get("/products", response_model=List[ProductResponse])
async def get_products():
    """Get all available products"""
    products = []
    for product_id, product in PRODUCTS.items():
        products.append(ProductResponse(
            id=product_id,
            name=product["name"],
            price=product["price"],
            credits=product.get("credits"),
            credits_per_month=product.get("credits_per_month"),
            description=product["description"],
            mode=product["mode"]
        ))
    return products


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe checkout session"""
    if data.product_type not in PRODUCTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produs invalid"
        )

    product = PRODUCTS[data.product_type]

    try:
        # Create Stripe checkout session
        if product["mode"] == "subscription":
            # For subscriptions, we need to create a price first or use price_id
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": product["price"],
                        "recurring": {"interval": product.get("interval", "month")},
                        "product_data": {
                            "name": product["name"],
                            "description": product["description"]
                        }
                    },
                    "quantity": 1
                }],
                mode="subscription",
                success_url=f"{stripe_settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{stripe_settings.FRONTEND_URL}/pricing?cancelled=true",
                client_reference_id=current_user.id,
                customer_email=current_user.email,
                metadata={
                    "product_type": data.product_type,
                    "user_id": current_user.id
                }
            )
        else:
            # One-time payment
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": product["price"],
                        "product_data": {
                            "name": product["name"],
                            "description": product["description"]
                        }
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=f"{stripe_settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{stripe_settings.FRONTEND_URL}/pricing?cancelled=true",
                client_reference_id=current_user.id,
                customer_email=current_user.email,
                metadata={
                    "product_type": data.product_type,
                    "user_id": current_user.id
                }
            )

        # Create pending payment record
        payment = Payment(
            user_id=current_user.id,
            stripe_session_id=session.id,
            amount=product["price"],
            currency="EUR",
            status="pending",
            product_type=data.product_type,
            credits_added=product.get("credits", 0)
        )
        db.add(payment)
        await db.commit()

        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eroare Stripe: {str(e)}"
        )


@router.post("/create-lead-checkout", response_model=CheckoutResponse)
async def create_lead_checkout(
    data: LeadCheckoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe checkout session for a lead (no login required)"""
    # Get lead
    result = await db.execute(
        select(Lead).where(Lead.id == data.lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    # Get package
    pkg_result = await db.execute(
        select(Package).where(Package.id == data.package_id)
    )
    package = pkg_result.scalar_one_or_none()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Package not found"
        )

    if package.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This package is free and doesn't require payment"
        )

    try:
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": package.currency.lower(),
                    "unit_amount": int(package.price * 100),  # Convert to cents
                    "product_data": {
                        "name": f"AI Web Auditor - {package.name} Package",
                        "description": f"Website audit report with {package.audits_included} audit types"
                    }
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{stripe_settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{stripe_settings.FRONTEND_URL}/?cancelled=true",
            customer_email=lead.email,
            metadata={
                "lead_id": lead.id,
                "package_id": data.package_id,
                "audit_id": lead.audit_id,
                "type": "lead_payment"
            }
        )

        # Update lead with session ID
        lead.stripe_session_id = session.id
        await db.commit()

        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            stripe_settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_checkout_completed(session, db)

    elif event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        await handle_invoice_paid(invoice, db)

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_cancelled(subscription, db)

    return {"received": True}


async def handle_checkout_completed(session: dict, db: AsyncSession):
    """Handle successful checkout"""
    metadata = session.get("metadata", {})

    # Check if this is a lead payment
    if metadata.get("type") == "lead_payment":
        await handle_lead_payment_completed(session, db)
        return

    user_id = session.get("client_reference_id") or metadata.get("user_id")
    product_type = metadata.get("product_type")

    if not user_id or not product_type:
        return

    product = PRODUCTS.get(product_type)
    if not product:
        return

    user_repo = UserRepository(db)

    # Update payment status
    result = await db.execute(
        select(Payment).where(Payment.stripe_session_id == session["id"])
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = "completed"
        payment.completed_at = datetime.utcnow()
        payment.stripe_payment_intent = session.get("payment_intent")

    # Add credits for one-time purchases
    if product["mode"] == "payment":
        credits = product.get("credits", 0)
        await user_repo.add_credits(user_id, credits)

    # Handle subscription
    elif product["mode"] == "subscription":
        # Create or update subscription record
        sub_id = session.get("subscription")
        customer_id = session.get("customer")

        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.stripe_subscription_id = sub_id
            subscription.stripe_customer_id = customer_id
            subscription.plan = product_type
            subscription.status = "active"
            subscription.credits_per_month = product.get("credits_per_month", 20)
        else:
            subscription = Subscription(
                user_id=user_id,
                stripe_subscription_id=sub_id,
                stripe_customer_id=customer_id,
                plan=product_type,
                status="active",
                credits_per_month=product.get("credits_per_month", 20)
            )
            db.add(subscription)

        # Add initial credits
        await user_repo.add_credits(user_id, product.get("credits_per_month", 20))

    await db.commit()


async def handle_lead_payment_completed(session: dict, db: AsyncSession):
    """Handle successful lead payment"""
    metadata = session.get("metadata", {})
    lead_id = metadata.get("lead_id")
    package_id = metadata.get("package_id")

    if not lead_id:
        return

    # Get lead
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        return

    # Update lead status
    lead.payment_status = "paid"
    lead.status = "converted"
    lead.converted_at = datetime.utcnow()

    # Generate invoice number
    from leads.router import generate_reference
    lead.invoice_number = f"INV-{generate_reference()[4:]}"  # INV-YYYYMMDD-XXXX

    await db.commit()

    # TODO: Send confirmation email with invoice
    # TODO: Send audit report email

    print(f"Lead payment completed: {lead_id}, package: {package_id}")


async def handle_invoice_paid(invoice: dict, db: AsyncSession):
    """Handle subscription renewal"""
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        # Add monthly credits
        user_repo = UserRepository(db)
        await user_repo.add_credits(subscription.user_id, subscription.credits_per_month)

        # Create payment record
        payment = Payment(
            user_id=subscription.user_id,
            stripe_payment_intent=invoice.get("payment_intent"),
            amount=invoice.get("amount_paid", 0),
            currency=invoice.get("currency", "eur").upper(),
            status="completed",
            product_type=subscription.plan,
            credits_added=subscription.credits_per_month,
            completed_at=datetime.utcnow()
        )
        db.add(payment)
        await db.commit()


async def handle_subscription_cancelled(subscription_data: dict, db: AsyncSession):
    """Handle subscription cancellation"""
    subscription_id = subscription_data.get("id")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        await db.commit()


@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's payment history"""
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(50)
    )
    payments = result.scalars().all()

    return [
        PaymentResponse(
            id=p.id,
            amount=p.amount,
            currency=p.currency,
            status=p.status,
            product_type=p.product_type,
            credits_added=p.credits_added,
            created_at=p.created_at.isoformat()
        )
        for p in payments
    ]


@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel user's subscription"""
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status == "active"
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nu aveti un abonament activ"
        )

    try:
        # Cancel in Stripe
        stripe.Subscription.delete(subscription.stripe_subscription_id)

        # Update local record
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        await db.commit()

        return {"message": "Abonament anulat cu succes"}

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eroare la anulare: {str(e)}"
        )
