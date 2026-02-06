"""
SQLAlchemy ORM models for AI Web Auditor
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .connection import Base


def generate_uuid():
    return str(uuid.uuid4())


# ============== USER MODEL ==============

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    role = Column(String(20), default="user")  # user, admin
    credits = Column(Integer, default=3)  # Free credits for new users
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    audits = relationship("Audit", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False)


# ============== AUDIT MODELS ==============

class Audit(Base):
    __tablename__ = "audits"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    url = Column(String(2048), nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    audit_types = Column(JSON, default=list)  # ["performance", "seo", ...]

    # Scores (0-100)
    overall_score = Column(Integer, default=0)
    performance_score = Column(Integer, nullable=True)
    seo_score = Column(Integer, nullable=True)
    security_score = Column(Integer, nullable=True)
    gdpr_score = Column(Integer, nullable=True)
    accessibility_score = Column(Integer, nullable=True)

    # Screenshots (base64 or URL)
    desktop_screenshot = Column(Text, nullable=True)
    mobile_screenshot = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audits")
    issues = relationship("AuditIssue", back_populates="audit", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="audit", uselist=False, cascade="all, delete-orphan")
    seo_metrics = relationship("SEOMetric", back_populates="audit", uselist=False, cascade="all, delete-orphan")
    security_metrics = relationship("SecurityMetric", back_populates="audit", uselist=False, cascade="all, delete-orphan")
    gdpr_metrics = relationship("GDPRMetric", back_populates="audit", uselist=False, cascade="all, delete-orphan")
    accessibility_metrics = relationship("AccessibilityMetric", back_populates="audit", uselist=False, cascade="all, delete-orphan")


class AuditIssue(Base):
    __tablename__ = "audit_issues"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audit_id = Column(String(36), ForeignKey("audits.id"), nullable=False, index=True)

    category = Column(String(50), nullable=False)  # performance, seo, security, gdpr, accessibility
    severity = Column(String(20), nullable=False)  # critical, high, medium, low, info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    affected_element = Column(Text, nullable=True)
    screenshot_url = Column(Text, nullable=True)

    # For pricing
    estimated_hours = Column(Float, default=1.0)
    complexity = Column(String(20), default="medium")  # simple, medium, complex

    # Relationship
    audit = relationship("Audit", back_populates="issues")


# ============== METRICS MODELS ==============

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audit_id = Column(String(36), ForeignKey("audits.id"), unique=True, nullable=False)

    score = Column(Integer, default=0)
    lcp = Column(Float, nullable=True)  # Largest Contentful Paint
    fid = Column(Float, nullable=True)  # First Input Delay
    cls = Column(Float, nullable=True)  # Cumulative Layout Shift
    ttfb = Column(Float, nullable=True)  # Time to First Byte
    speed_index = Column(Float, nullable=True)
    total_blocking_time = Column(Float, nullable=True)
    first_contentful_paint = Column(Float, nullable=True)

    audit = relationship("Audit", back_populates="performance_metrics")


class SEOMetric(Base):
    __tablename__ = "seo_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audit_id = Column(String(36), ForeignKey("audits.id"), unique=True, nullable=False)

    score = Column(Integer, default=0)
    title = Column(String(255), nullable=True)
    title_length = Column(Integer, default=0)
    meta_description = Column(Text, nullable=True)
    meta_description_length = Column(Integer, default=0)
    h1_count = Column(Integer, default=0)
    h1_texts = Column(JSON, default=list)
    canonical_url = Column(String(2048), nullable=True)
    robots_txt_exists = Column(Boolean, default=False)
    sitemap_exists = Column(Boolean, default=False)
    structured_data = Column(JSON, default=list)
    broken_links = Column(JSON, default=list)
    image_alt_missing = Column(Integer, default=0)

    audit = relationship("Audit", back_populates="seo_metrics")


class SecurityMetric(Base):
    __tablename__ = "security_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audit_id = Column(String(36), ForeignKey("audits.id"), unique=True, nullable=False)

    score = Column(Integer, default=0)
    https_enabled = Column(Boolean, default=False)
    ssl_valid = Column(Boolean, default=False)
    ssl_expiry_days = Column(Integer, nullable=True)
    hsts_enabled = Column(Boolean, default=False)
    csp_enabled = Column(Boolean, default=False)
    x_frame_options = Column(Boolean, default=False)
    x_content_type_options = Column(Boolean, default=False)
    cookies_secure = Column(Boolean, default=False)
    cookies_httponly = Column(Boolean, default=False)
    exposed_emails = Column(JSON, default=list)
    exposed_api_keys = Column(Boolean, default=False)

    audit = relationship("Audit", back_populates="security_metrics")


class GDPRMetric(Base):
    __tablename__ = "gdpr_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audit_id = Column(String(36), ForeignKey("audits.id"), unique=True, nullable=False)

    score = Column(Integer, default=0)
    cookie_banner_present = Column(Boolean, default=False)
    privacy_policy_link = Column(Boolean, default=False)
    cookie_categories_explained = Column(Boolean, default=False)
    opt_out_option = Column(Boolean, default=False)
    third_party_trackers = Column(JSON, default=list)
    google_analytics = Column(Boolean, default=False)
    facebook_pixel = Column(Boolean, default=False)
    data_retention_info = Column(Boolean, default=False)

    audit = relationship("Audit", back_populates="gdpr_metrics")


class AccessibilityMetric(Base):
    __tablename__ = "accessibility_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    audit_id = Column(String(36), ForeignKey("audits.id"), unique=True, nullable=False)

    score = Column(Integer, default=0)
    wcag_level = Column(String(10), default="A")  # A, AA, AAA
    color_contrast_issues = Column(Integer, default=0)
    missing_alt_texts = Column(Integer, default=0)
    missing_form_labels = Column(Integer, default=0)
    keyboard_navigation = Column(Boolean, default=False)
    aria_usage = Column(Integer, default=0)
    heading_hierarchy_valid = Column(Boolean, default=False)

    audit = relationship("Audit", back_populates="accessibility_metrics")


# ============== PAYMENT MODELS ==============

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    stripe_session_id = Column(String(255), nullable=True)
    stripe_payment_intent = Column(String(255), nullable=True)

    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="EUR")
    status = Column(String(20), default="pending")  # pending, completed, failed, refunded
    product_type = Column(String(50), nullable=True)  # single, pack_5, pack_10, pack_20
    credits_added = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)

    plan = Column(String(50), default="monthly")  # monthly, yearly
    status = Column(String(20), default="active")  # active, cancelled, past_due
    credits_per_month = Column(Integer, default=20)

    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscription")
