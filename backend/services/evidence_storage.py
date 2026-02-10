"""
AI Web Auditor — Evidence Storage Service v1
S3-compatible object storage for audit evidence (screenshots, snippets).
Reference: DEV_DECISIONS_v1.md §3

Supports: AWS S3 / Cloudflare R2 / DigitalOcean Spaces.
Configure via environment variables:
  EVIDENCE_STORAGE_ENDPOINT  — S3-compatible endpoint URL
  EVIDENCE_STORAGE_BUCKET    — bucket name
  EVIDENCE_STORAGE_KEY_ID    — access key ID
  EVIDENCE_STORAGE_KEY_SECRET — secret key
  EVIDENCE_STORAGE_REGION    — region (default: auto)
  EVIDENCE_STORAGE_PUBLIC_URL — public base URL for presigned-free access (optional)
"""

from __future__ import annotations

import os
import io
import gzip
from datetime import datetime, timezone
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig


# ── Config ────────────────────────────────────────────────────────────

ENDPOINT = os.getenv("EVIDENCE_STORAGE_ENDPOINT", "")
BUCKET = os.getenv("EVIDENCE_STORAGE_BUCKET", "ave-evidence")
KEY_ID = os.getenv("EVIDENCE_STORAGE_KEY_ID", "")
KEY_SECRET = os.getenv("EVIDENCE_STORAGE_KEY_SECRET", "")
REGION = os.getenv("EVIDENCE_STORAGE_REGION", "auto")
PUBLIC_URL = os.getenv("EVIDENCE_STORAGE_PUBLIC_URL", "")

# Retention days
RETENTION_FREE = 30
RETENTION_UNLOCKED = 90


def _get_client():
    """Lazy-create S3 client (compatible with R2/Spaces)."""
    if not ENDPOINT or not KEY_ID:
        return None

    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=KEY_ID,
        aws_secret_access_key=KEY_SECRET,
        region_name=REGION,
        config=BotoConfig(signature_version="s3v4"),
    )


def is_configured() -> bool:
    """Check if evidence storage is configured."""
    return bool(ENDPOINT and KEY_ID and KEY_SECRET)


# ── Path helpers ──────────────────────────────────────────────────────

def _evidence_key(
    audit_id: str,
    component_id: str,
    check_id: str,
    filename: str,
) -> str:
    """Build S3 object key: audits/{auditId}/{componentId}/{checkId}/{filename}"""
    return f"audits/{audit_id}/{component_id}/{check_id}/{filename}"


# ── Upload ────────────────────────────────────────────────────────────

def upload_screenshot(
    audit_id: str,
    component_id: str,
    check_id: str,
    image_bytes: bytes,
    filename: str = "fullpage.webp",
    content_type: str = "image/webp",
) -> Optional[str]:
    """
    Upload a screenshot to evidence storage.
    Returns the public URL or object key, or None if storage not configured.
    """
    client = _get_client()
    if not client:
        return None

    key = _evidence_key(audit_id, component_id, check_id, filename)

    client.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,
        Metadata={
            "auditId": audit_id,
            "componentId": component_id,
            "checkId": check_id,
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
        },
    )

    if PUBLIC_URL:
        return f"{PUBLIC_URL.rstrip('/')}/{key}"
    return key


def upload_snippet(
    audit_id: str,
    component_id: str,
    check_id: str,
    html_content: str,
    filename: str = "snippet.html.gz",
) -> Optional[str]:
    """
    Upload an HTML snippet (gzipped) to evidence storage.
    Returns URL/key or None.
    """
    client = _get_client()
    if not client:
        return None

    key = _evidence_key(audit_id, component_id, check_id, filename)

    compressed = gzip.compress(html_content.encode("utf-8"))

    client.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=compressed,
        ContentType="application/gzip",
        ContentEncoding="gzip",
        Metadata={
            "auditId": audit_id,
            "componentId": component_id,
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
        },
    )

    if PUBLIC_URL:
        return f"{PUBLIC_URL.rstrip('/')}/{key}"
    return key


def upload_file(
    audit_id: str,
    component_id: str,
    check_id: str,
    file_bytes: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
) -> Optional[str]:
    """Generic file upload to evidence storage."""
    client = _get_client()
    if not client:
        return None

    key = _evidence_key(audit_id, component_id, check_id, filename)

    client.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
        Metadata={
            "auditId": audit_id,
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
        },
    )

    if PUBLIC_URL:
        return f"{PUBLIC_URL.rstrip('/')}/{key}"
    return key


# ── Download / presigned URL ──────────────────────────────────────────

def get_presigned_url(key: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a presigned URL for private evidence access."""
    client = _get_client()
    if not client:
        return None

    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )


# ── Cleanup / retention ──────────────────────────────────────────────

def delete_audit_evidence(audit_id: str) -> int:
    """Delete all evidence for an audit. Returns number of objects deleted."""
    client = _get_client()
    if not client:
        return 0

    prefix = f"audits/{audit_id}/"
    deleted = 0

    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        objects = page.get("Contents", [])
        if not objects:
            continue

        delete_request = {
            "Objects": [{"Key": obj["Key"]} for obj in objects],
            "Quiet": True,
        }
        client.delete_objects(Bucket=BUCKET, Delete=delete_request)
        deleted += len(objects)

    return deleted


def configure_bucket_lifecycle():
    """
    Set up lifecycle rules for evidence retention.
    Call once during setup or deployment.

    Rules:
    - Tag 'retention=free': delete after 30 days
    - Tag 'retention=unlocked': delete after 90 days
    """
    client = _get_client()
    if not client:
        return

    client.put_bucket_lifecycle_configuration(
        Bucket=BUCKET,
        LifecycleConfiguration={
            "Rules": [
                {
                    "ID": "free-preview-retention",
                    "Filter": {"Tag": {"Key": "retention", "Value": "free"}},
                    "Status": "Enabled",
                    "Expiration": {"Days": RETENTION_FREE},
                },
                {
                    "ID": "unlocked-report-retention",
                    "Filter": {"Tag": {"Key": "retention", "Value": "unlocked"}},
                    "Status": "Enabled",
                    "Expiration": {"Days": RETENTION_UNLOCKED},
                },
            ]
        },
    )
