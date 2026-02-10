"""
AI Web Auditor — Email Scheduler v1
Background task that sends nudge and reminder emails for un-unlocked audits.
Reference: DEV_DECISIONS_v1.md §5

Schedule:
  - Unlock nudge: 45 min after audit completes (if not unlocked)
  - Reminder: 24h after audit completes (if not unlocked)

Run as a background loop or via cron (e.g., every 15 minutes).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session
from database.models import Audit, Lead, AuditLog
from services.email_service import send_unlock_nudge, send_reminder


# Timing thresholds
NUDGE_AFTER_MINUTES = 45
NUDGE_WINDOW_MINUTES = 90   # Don't send nudge if older than this
REMINDER_AFTER_HOURS = 24
REMINDER_WINDOW_HOURS = 48  # Don't send reminder if older than this

# Poll interval when running as continuous loop
POLL_INTERVAL_SECONDS = 900  # 15 minutes


async def check_and_send_emails():
    """
    Check for completed audits that haven't been unlocked
    and send appropriate follow-up emails.
    """
    async with async_session() as db:
        now = datetime.now(timezone.utc)

        # Find completed audits with no unlock (no Lead record)
        completed_audits = await db.execute(
            select(Audit)
            .where(
                Audit.status == "completed",
                Audit.completed_at.isnot(None),
            )
            .order_by(Audit.completed_at.desc())
            .limit(100)
        )
        audits = completed_audits.scalars().all()

        for audit in audits:
            completed_at = audit.completed_at
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)

            age = now - completed_at

            # Check if already unlocked
            lead_result = await db.execute(
                select(Lead).where(Lead.audit_id == audit.id).limit(1)
            )
            lead = lead_result.scalar_one_or_none()
            if lead:
                continue  # Already unlocked, skip

            # Find email (from audit log or other source)
            email = await _find_audit_email(db, audit.id)
            if not email:
                continue

            # Check what's already been sent
            sent_nudge = await _email_already_sent(db, audit.id, "nudge_sent")
            sent_reminder = await _email_already_sent(db, audit.id, "reminder_sent")

            # Send nudge (45-90 min after completion)
            if (not sent_nudge
                and timedelta(minutes=NUDGE_AFTER_MINUTES) <= age <= timedelta(minutes=NUDGE_WINDOW_MINUTES)):
                success = send_unlock_nudge(email, audit.url, audit.id)
                if success:
                    await _log_email_sent(db, audit.id, email, "nudge_sent")

            # Send reminder (24-48h after completion)
            elif (not sent_reminder
                  and timedelta(hours=REMINDER_AFTER_HOURS) <= age <= timedelta(hours=REMINDER_WINDOW_HOURS)):
                success = send_reminder(email, audit.url, audit.id)
                if success:
                    await _log_email_sent(db, audit.id, email, "reminder_sent")

        await db.commit()


async def _find_audit_email(db: AsyncSession, audit_id: str) -> str | None:
    """Find the email associated with an audit (from audit log)."""
    result = await db.execute(
        select(AuditLog.email)
        .where(
            AuditLog.entity_id == audit_id,
            AuditLog.email.isnot(None),
        )
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row


async def _email_already_sent(db: AsyncSession, audit_id: str, action: str) -> bool:
    """Check if a specific email was already sent for this audit."""
    result = await db.execute(
        select(AuditLog)
        .where(
            and_(
                AuditLog.action == action,
                AuditLog.entity_type == "audit",
                AuditLog.entity_id == audit_id,
            )
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _log_email_sent(db: AsyncSession, audit_id: str, email: str, action: str):
    """Record that an email was sent."""
    log = AuditLog(
        action=action,
        entity_type="audit",
        entity_id=audit_id,
        email=email,
        details={"sentAt": datetime.now(timezone.utc).isoformat()},
    )
    db.add(log)


async def run_email_scheduler_loop():
    """Run the email scheduler as a continuous background loop."""
    print("[EMAIL SCHEDULER] Starting...")
    while True:
        try:
            await check_and_send_emails()
        except Exception as e:
            print(f"[EMAIL SCHEDULER] Error: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
