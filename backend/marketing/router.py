"""
Marketing Automation API
Webhook integrations for CRM, email marketing, and automation platforms
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import hmac
import hashlib
import json

from database.connection import get_db
from database.models import User, Lead, AuditLog
from auth.dependencies import get_current_user, require_admin


router = APIRouter(prefix="/api/marketing", tags=["marketing"])


# ============== SCHEMAS ==============

class WebhookConfig(BaseModel):
    id: Optional[str] = None
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None
    is_active: bool = True
    headers: Optional[dict] = None


class WebhookEvent(BaseModel):
    event: str
    timestamp: str
    data: dict


class EmailTemplate(BaseModel):
    id: str
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    trigger: str  # lead_created, payment_completed, etc.
    is_active: bool = True


class MarketingSettings(BaseModel):
    webhooks: List[WebhookConfig]
    email_templates: List[EmailTemplate]
    crm_integration: Optional[dict] = None


# ============== WEBHOOK STORAGE (in production, use database) ==============

# In-memory storage for webhooks (should be in DB for production)
WEBHOOKS: List[WebhookConfig] = []

# Supported events
SUPPORTED_EVENTS = [
    "lead.created",
    "lead.verified",
    "lead.converted",
    "audit.completed",
    "payment.completed",
    "payment.failed",
    "social_share.completed"
]


# ============== HELPER FUNCTIONS ==============

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC signature for webhook payload"""
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


async def send_webhook(webhook: WebhookConfig, event: str, data: dict):
    """Send webhook to configured URL"""
    payload = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event,
        "X-Webhook-Timestamp": datetime.utcnow().isoformat()
    }

    # Add custom headers
    if webhook.headers:
        headers.update(webhook.headers)

    # Add signature if secret is configured
    if webhook.secret:
        payload_str = json.dumps(payload, sort_keys=True)
        signature = generate_signature(payload_str, webhook.secret)
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook.url,
                json=payload,
                headers=headers
            )
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "webhook_id": webhook.id
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "webhook_id": webhook.id
        }


async def trigger_webhooks(event: str, data: dict, db: AsyncSession):
    """Trigger all webhooks for a specific event"""
    results = []

    for webhook in WEBHOOKS:
        if not webhook.is_active:
            continue
        if event not in webhook.events and "*" not in webhook.events:
            continue

        result = await send_webhook(webhook, event, data)
        results.append(result)

        # Log webhook call
        log = AuditLog(
            action="webhook_sent",
            entity_type="webhook",
            entity_id=webhook.id,
            details={
                "event": event,
                "url": webhook.url,
                "success": result.get("success", False),
                "status_code": result.get("status_code"),
                "error": result.get("error")
            }
        )
        db.add(log)

    await db.commit()
    return results


# ============== PUBLIC TRIGGER FUNCTIONS ==============

async def on_lead_created(lead: Lead, db: AsyncSession):
    """Trigger webhooks when a new lead is created"""
    await trigger_webhooks("lead.created", {
        "lead_id": lead.id,
        "reference": lead.reference,
        "email": lead.email,
        "name": lead.name,
        "language": lead.language,
        "package_id": lead.package_id,
        "url": lead.url,
        "created_at": lead.created_at.isoformat() if lead.created_at else None
    }, db)


async def on_lead_converted(lead: Lead, db: AsyncSession):
    """Trigger webhooks when a lead converts (payment completed)"""
    await trigger_webhooks("lead.converted", {
        "lead_id": lead.id,
        "reference": lead.reference,
        "email": lead.email,
        "name": lead.name,
        "package_id": lead.package_id,
        "payment_status": lead.payment_status,
        "converted_at": lead.converted_at.isoformat() if lead.converted_at else None
    }, db)


async def on_audit_completed(audit_id: str, url: str, scores: dict, db: AsyncSession):
    """Trigger webhooks when an audit completes"""
    await trigger_webhooks("audit.completed", {
        "audit_id": audit_id,
        "url": url,
        "scores": scores
    }, db)


async def on_payment_completed(lead_id: str, amount: float, currency: str, db: AsyncSession):
    """Trigger webhooks when payment is completed"""
    await trigger_webhooks("payment.completed", {
        "lead_id": lead_id,
        "amount": amount,
        "currency": currency,
        "timestamp": datetime.utcnow().isoformat()
    }, db)


# ============== API ENDPOINTS ==============

@router.get("/webhooks")
async def list_webhooks(admin = Depends(require_admin)):
    """List all configured webhooks"""
    return WEBHOOKS


@router.post("/webhooks")
async def create_webhook(
    webhook: WebhookConfig,
    admin = Depends(require_admin)
):
    """Create a new webhook"""
    import uuid

    webhook.id = str(uuid.uuid4())

    # Validate events
    for event in webhook.events:
        if event != "*" and event not in SUPPORTED_EVENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported event: {event}. Supported: {SUPPORTED_EVENTS}"
            )

    WEBHOOKS.append(webhook)
    return webhook


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    admin = Depends(require_admin)
):
    """Delete a webhook"""
    global WEBHOOKS
    WEBHOOKS = [w for w in WEBHOOKS if w.id != webhook_id]
    return {"success": True}


@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    admin = Depends(require_admin)
):
    """Test a webhook with sample data"""
    webhook = next((w for w in WEBHOOKS if w.id == webhook_id), None)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    test_data = {
        "test": True,
        "message": "This is a test webhook from AI Web Auditor",
        "timestamp": datetime.utcnow().isoformat()
    }

    result = await send_webhook(webhook, "test", test_data)
    return result


@router.get("/events")
async def list_supported_events():
    """List all supported webhook events"""
    return {
        "events": SUPPORTED_EVENTS,
        "descriptions": {
            "lead.created": "Triggered when a new lead is created",
            "lead.verified": "Triggered when lead email is verified",
            "lead.converted": "Triggered when lead completes payment",
            "audit.completed": "Triggered when an audit finishes",
            "payment.completed": "Triggered when payment succeeds",
            "payment.failed": "Triggered when payment fails",
            "social_share.completed": "Triggered when social share is verified"
        }
    }


# ============== ZAPIER / N8N INTEGRATION ENDPOINTS ==============

@router.get("/zapier/subscribe")
async def zapier_subscribe_info():
    """Info endpoint for Zapier integration"""
    return {
        "name": "AI Web Auditor",
        "description": "Website auditing platform with lead capture",
        "subscribe_url": "/api/marketing/webhooks",
        "events": SUPPORTED_EVENTS
    }


@router.post("/zapier/hook")
async def zapier_hook_handler(request: Request):
    """Handle incoming Zapier hooks (for 2-way integration)"""
    data = await request.json()
    # Process Zapier action (e.g., update lead status)
    return {"received": True, "data": data}


# ============== CRM INTEGRATION ==============

class CRMConfig(BaseModel):
    provider: str  # hubspot, salesforce, pipedrive, etc.
    api_key: str
    settings: Optional[dict] = None


# In-memory CRM config (should be in DB)
CRM_CONFIG: Optional[CRMConfig] = None


@router.get("/crm/config")
async def get_crm_config(admin = Depends(require_admin)):
    """Get current CRM configuration"""
    if not CRM_CONFIG:
        return {"configured": False}
    return {
        "configured": True,
        "provider": CRM_CONFIG.provider,
        "settings": CRM_CONFIG.settings
    }


@router.post("/crm/config")
async def set_crm_config(
    config: CRMConfig,
    admin = Depends(require_admin)
):
    """Configure CRM integration"""
    global CRM_CONFIG
    CRM_CONFIG = config
    return {"success": True, "provider": config.provider}


async def sync_lead_to_crm(lead: Lead):
    """Sync a lead to configured CRM"""
    if not CRM_CONFIG:
        return

    if CRM_CONFIG.provider == "hubspot":
        await sync_to_hubspot(lead)
    elif CRM_CONFIG.provider == "pipedrive":
        await sync_to_pipedrive(lead)
    # Add more CRM providers as needed


async def sync_to_hubspot(lead: Lead):
    """Sync lead to HubSpot"""
    if not CRM_CONFIG or CRM_CONFIG.provider != "hubspot":
        return

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={
                "Authorization": f"Bearer {CRM_CONFIG.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "properties": {
                    "email": lead.email,
                    "firstname": lead.name.split()[0] if lead.name else "",
                    "lastname": " ".join(lead.name.split()[1:]) if lead.name and len(lead.name.split()) > 1 else "",
                    "website": lead.url,
                    "ai_web_auditor_reference": lead.reference,
                    "ai_web_auditor_package": lead.package_id,
                    "lifecyclestage": "lead"
                }
            }
        )
        return response.json()


async def sync_to_pipedrive(lead: Lead):
    """Sync lead to Pipedrive"""
    if not CRM_CONFIG or CRM_CONFIG.provider != "pipedrive":
        return

    async with httpx.AsyncClient() as client:
        # Create person
        person_response = await client.post(
            f"https://api.pipedrive.com/v1/persons?api_token={CRM_CONFIG.api_key}",
            json={
                "name": lead.name,
                "email": lead.email
            }
        )
        person_data = person_response.json()

        if person_data.get("success"):
            # Create deal
            await client.post(
                f"https://api.pipedrive.com/v1/deals?api_token={CRM_CONFIG.api_key}",
                json={
                    "title": f"AI Web Auditor - {lead.reference}",
                    "person_id": person_data["data"]["id"],
                    "value": 1.99 if lead.package_id == "pro" else 4.99 if lead.package_id == "full" else 0,
                    "currency": "EUR"
                }
            )


# ============== EMAIL AUTOMATION ==============

EMAIL_TEMPLATES: List[EmailTemplate] = [
    EmailTemplate(
        id="welcome",
        name="Welcome Email",
        subject="Welcome to AI Web Auditor!",
        body_html="<h1>Welcome {{name}}!</h1><p>Thank you for your interest in AI Web Auditor.</p>",
        trigger="lead.created",
        is_active=True
    ),
    EmailTemplate(
        id="audit_complete",
        name="Audit Complete",
        subject="Your Website Audit is Ready",
        body_html="<h1>Hi {{name}},</h1><p>Your audit for {{url}} is complete with a score of {{score}}.</p>",
        trigger="audit.completed",
        is_active=True
    ),
    EmailTemplate(
        id="payment_success",
        name="Payment Success",
        subject="Payment Confirmed - Your Full Report is Ready",
        body_html="<h1>Thank you {{name}}!</h1><p>Your payment has been processed. Access your full report now.</p>",
        trigger="payment.completed",
        is_active=True
    )
]


@router.get("/email-templates")
async def list_email_templates(admin = Depends(require_admin)):
    """List all email templates"""
    return EMAIL_TEMPLATES


@router.patch("/email-templates/{template_id}")
async def update_email_template(
    template_id: str,
    update: dict,
    admin = Depends(require_admin)
):
    """Update an email template"""
    for template in EMAIL_TEMPLATES:
        if template.id == template_id:
            for key, value in update.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            return template

    raise HTTPException(status_code=404, detail="Template not found")
