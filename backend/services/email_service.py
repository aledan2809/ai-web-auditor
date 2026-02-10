"""
AI Web Auditor — Email Service v1 (SendGrid)
Transactional emails for the AVE landing page funnel.
Reference: DEV_DECISIONS_v1.md §5

Templates:
  1) Preview ready (immediate after audit completes)
  2) Unlock nudge (30-60 min after preview, if not unlocked)
  3) Reminder (24h after preview, if not unlocked)

Configure via environment:
  SENDGRID_API_KEY
  SENDGRID_FROM_EMAIL (default: support@techbiz.ae)
  SENDGRID_FROM_NAME  (default: AVE by TechBiz)
"""

from __future__ import annotations

import os
from typing import Optional
from datetime import datetime, timezone

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, Content, MimeType


# ── Config ────────────────────────────────────────────────────────────

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "support@techbiz.ae")
FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "AVE by TechBiz")

# Internal notification recipient
ADMIN_EMAIL = os.getenv("AVE_ADMIN_EMAIL", "alexdanciulescu@gmail.com")

# Base URL for links in emails
BASE_URL = os.getenv("AVE_BASE_URL", "https://www.techbiz.ae/ave")


def is_configured() -> bool:
    return bool(SENDGRID_API_KEY)


def _get_client() -> Optional[SendGridAPIClient]:
    if not SENDGRID_API_KEY:
        return None
    return SendGridAPIClient(api_key=SENDGRID_API_KEY)


# ── Email templates (inline HTML for v1) ─────────────────────────────

def _base_html(content: str) -> str:
    """Wrap content in a clean email template."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#f5f5f5;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;">
  <tr><td style="background:#1a1a2e;padding:24px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:24px;">AVE</h1>
    <p style="color:#a0a0c0;margin:4px 0 0;font-size:13px;">AI Website Audit</p>
  </td></tr>
  <tr><td style="padding:32px 24px;">
    {content}
  </td></tr>
  <tr><td style="background:#f0f0f5;padding:16px 24px;text-align:center;font-size:12px;color:#888;">
    <p>TechBiz Hub L.L.C-FZ &bull; Meydan Grandstand, 6th floor, Dubai, U.A.E.</p>
    <p>WhatsApp: +971 52 901 6540 &bull; support@techbiz.ae</p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _preview_ready_html(website_url: str, audit_id: str, overall_score: int) -> str:
    teaser_link = f"{BASE_URL}?auditId={audit_id}"
    score_color = "#22c55e" if overall_score >= 75 else "#f59e0b" if overall_score >= 55 else "#ef4444"

    return _base_html(f"""
    <h2 style="margin:0 0 16px;color:#1a1a2e;">Your website audit is ready!</h2>
    <p style="color:#555;line-height:1.6;">
      We've completed the audit for <strong>{website_url}</strong>.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <div style="display:inline-block;width:100px;height:100px;border-radius:50%;border:6px solid {score_color};line-height:100px;font-size:32px;font-weight:bold;color:{score_color};">
        {overall_score}
      </div>
      <p style="color:#888;margin:8px 0 0;">Overall Score</p>
    </div>
    <p style="color:#555;line-height:1.6;">
      We found areas where your site can improve in performance, SEO, security, and more.
      View your free preview to see the top issues.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{teaser_link}" style="display:inline-block;background:#4f46e5;color:#fff;padding:14px 32px;border-radius:6px;text-decoration:none;font-weight:bold;">
        View Your Free Preview
      </a>
    </div>
    """)


def _unlock_nudge_html(website_url: str, audit_id: str) -> str:
    teaser_link = f"{BASE_URL}?auditId={audit_id}"

    return _base_html(f"""
    <h2 style="margin:0 0 16px;color:#1a1a2e;">Your audit results are waiting</h2>
    <p style="color:#555;line-height:1.6;">
      You started an audit for <strong>{website_url}</strong> but haven't unlocked the full report yet.
    </p>
    <p style="color:#555;line-height:1.6;">
      The full report includes all 9 audit components, detailed issue descriptions,
      fix recommendations, and a prioritized action plan.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{teaser_link}" style="display:inline-block;background:#4f46e5;color:#fff;padding:14px 32px;border-radius:6px;text-decoration:none;font-weight:bold;">
        Unlock Full Report
      </a>
    </div>
    <p style="color:#888;font-size:13px;">
      Questions? Reply to this email or WhatsApp us at +971 52 901 6540.
    </p>
    """)


def _reminder_html(website_url: str, audit_id: str) -> str:
    teaser_link = f"{BASE_URL}?auditId={audit_id}"

    return _base_html(f"""
    <h2 style="margin:0 0 16px;color:#1a1a2e;">Last reminder: your audit report</h2>
    <p style="color:#555;line-height:1.6;">
      We audited <strong>{website_url}</strong> yesterday and found issues that may be
      affecting your traffic and conversions.
    </p>
    <p style="color:#555;line-height:1.6;">
      Unlock the full report to see exactly what needs fixing, with estimated time
      and priority for each issue.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{teaser_link}" style="display:inline-block;background:#4f46e5;color:#fff;padding:14px 32px;border-radius:6px;text-decoration:none;font-weight:bold;">
        View Full Report
      </a>
    </div>
    <p style="color:#888;font-size:13px;">
      Not interested? No worries — we won't email you again about this audit.
    </p>
    """)


# ── Send functions ────────────────────────────────────────────────────

def _send(to_email: str, subject: str, html: str) -> bool:
    """Send an email. Returns True on success."""
    client = _get_client()
    if not client:
        print(f"[EMAIL] SendGrid not configured. Would send to {to_email}: {subject}")
        return False

    message = Mail(
        from_email=From(FROM_EMAIL, FROM_NAME),
        to_emails=To(to_email),
        subject=Subject(subject),
        html_content=Content(MimeType.html, html),
    )

    try:
        response = client.send(message)
        print(f"[EMAIL] Sent to {to_email}: {subject} (status={response.status_code})")
        return 200 <= response.status_code < 300
    except Exception as e:
        print(f"[EMAIL] Error sending to {to_email}: {e}")
        return False


def send_preview_ready(
    to_email: str,
    website_url: str,
    audit_id: str,
    overall_score: int,
) -> bool:
    """Send 'preview ready' email immediately after audit completes."""
    html = _preview_ready_html(website_url, audit_id, overall_score)
    return _send(to_email, f"Your website audit is ready — Score: {overall_score}/100", html)


def send_unlock_nudge(
    to_email: str,
    website_url: str,
    audit_id: str,
) -> bool:
    """Send 'unlock nudge' email (30-60 min after preview, if not unlocked)."""
    html = _unlock_nudge_html(website_url, audit_id)
    return _send(to_email, "Your full audit report is waiting", html)


def send_reminder(
    to_email: str,
    website_url: str,
    audit_id: str,
) -> bool:
    """Send '24h reminder' email (if not unlocked)."""
    html = _reminder_html(website_url, audit_id)
    return _send(to_email, "Last reminder: your website audit report", html)


# ── Admin notifications ──────────────────────────────────────────────

def send_admin_new_audit(website_url: str, audit_id: str, email: Optional[str] = None) -> bool:
    """Notify admin about new audit started."""
    html = _base_html(f"""
    <h2 style="margin:0 0 16px;color:#1a1a2e;">New AVE Audit Started</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px;color:#888;">URL:</td><td style="padding:8px;"><strong>{website_url}</strong></td></tr>
      <tr><td style="padding:8px;color:#888;">Audit ID:</td><td style="padding:8px;">{audit_id}</td></tr>
      <tr><td style="padding:8px;color:#888;">Email:</td><td style="padding:8px;">{email or 'Not provided'}</td></tr>
      <tr><td style="padding:8px;color:#888;">Time:</td><td style="padding:8px;">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</td></tr>
    </table>
    """)
    return _send(ADMIN_EMAIL, f"[AVE] New audit: {website_url}", html)


def send_admin_unlock(website_url: str, audit_id: str, email: str, lead_id: str) -> bool:
    """Notify admin about report unlock."""
    html = _base_html(f"""
    <h2 style="margin:0 0 16px;color:#22c55e;">Report Unlocked!</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px;color:#888;">URL:</td><td style="padding:8px;"><strong>{website_url}</strong></td></tr>
      <tr><td style="padding:8px;color:#888;">Email:</td><td style="padding:8px;"><strong>{email}</strong></td></tr>
      <tr><td style="padding:8px;color:#888;">Lead ID:</td><td style="padding:8px;">{lead_id}</td></tr>
      <tr><td style="padding:8px;color:#888;">Audit ID:</td><td style="padding:8px;">{audit_id}</td></tr>
    </table>
    """)
    return _send(ADMIN_EMAIL, f"[AVE] Unlocked: {email} — {website_url}", html)
