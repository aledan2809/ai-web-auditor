"""
Pydantic models for AI Web Auditor
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AuditType(str, Enum):
    PERFORMANCE = "performance"
    SEO = "seo"
    SECURITY = "security"
    GDPR = "gdpr"
    ACCESSIBILITY = "accessibility"
    UI_UX = "ui_ux"
    API = "api"
    FULL = "full"


class AuditStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Request Models
class AuditRequest(BaseModel):
    url: HttpUrl
    audit_types: List[AuditType] = [AuditType.FULL]
    include_screenshots: bool = True
    mobile_test: bool = True
    competitor_urls: List[HttpUrl] = []
    lang: str = "ro"  # "ro" or "en"


class APITestRequest(BaseModel):
    base_url: HttpUrl
    endpoints: List[Dict[str, Any]]  # [{method, path, headers, body}]
    auth_token: Optional[str] = None


class EstimateRequest(BaseModel):
    audit_id: str
    hourly_rate: float = 75.0  # EUR/hour
    currency: str = "EUR"


# Issue Models
class AuditIssue(BaseModel):
    id: str
    category: AuditType
    severity: Severity
    title: str
    description: str
    recommendation: str
    affected_element: Optional[str] = None
    screenshot_url: Optional[str] = None

    # For pricing
    estimated_hours: float = 1.0
    complexity: str = "medium"  # simple, medium, complex


class PerformanceMetrics(BaseModel):
    score: int = Field(ge=0, le=100)
    lcp: float  # Largest Contentful Paint (seconds)
    fid: float  # First Input Delay (ms)
    cls: float  # Cumulative Layout Shift
    ttfb: float  # Time to First Byte (ms)
    speed_index: float
    total_blocking_time: float
    first_contentful_paint: float


class SEOMetrics(BaseModel):
    score: int = Field(ge=0, le=100)
    title: Optional[str]
    title_length: int
    meta_description: Optional[str]
    meta_description_length: int
    h1_count: int
    h1_texts: List[str]
    canonical_url: Optional[str]
    robots_txt_exists: bool
    sitemap_exists: bool
    structured_data: List[str]
    broken_links: List[str]
    image_alt_missing: int


class SecurityMetrics(BaseModel):
    score: int = Field(ge=0, le=100)
    https_enabled: bool
    ssl_valid: bool
    ssl_expiry_days: Optional[int]
    hsts_enabled: bool
    csp_enabled: bool
    x_frame_options: bool
    x_content_type_options: bool
    cookies_secure: bool
    cookies_httponly: bool
    exposed_emails: List[str]
    exposed_api_keys: bool


class GDPRMetrics(BaseModel):
    score: int = Field(ge=0, le=100)
    cookie_banner_present: bool
    privacy_policy_link: bool
    cookie_categories_explained: bool
    opt_out_option: bool
    third_party_trackers: List[str]
    google_analytics: bool
    facebook_pixel: bool
    data_retention_info: bool


class AccessibilityMetrics(BaseModel):
    score: int = Field(ge=0, le=100)
    wcag_level: str  # A, AA, AAA
    color_contrast_issues: int
    missing_alt_texts: int
    missing_form_labels: int
    keyboard_navigation: bool
    aria_usage: int
    heading_hierarchy_valid: bool


# Response Models
class AuditResult(BaseModel):
    id: str
    url: str
    status: AuditStatus
    created_at: datetime
    completed_at: Optional[datetime]

    # Scores (0-100)
    overall_score: int = 0
    performance_score: Optional[int]
    seo_score: Optional[int]
    security_score: Optional[int]
    gdpr_score: Optional[int]
    accessibility_score: Optional[int]

    # Detailed metrics
    performance: Optional[PerformanceMetrics]
    seo: Optional[SEOMetrics]
    security: Optional[SecurityMetrics]
    gdpr: Optional[GDPRMetrics]
    accessibility: Optional[AccessibilityMetrics]

    # Issues found
    issues: List[AuditIssue] = []

    # Screenshots
    desktop_screenshot: Optional[str]
    mobile_screenshot: Optional[str]


class PriceEstimate(BaseModel):
    audit_id: str
    total_issues: int
    issues_by_severity: Dict[str, int]

    # Time estimates
    total_hours: float
    hours_by_category: Dict[str, float]

    # Price estimates
    currency: str
    hourly_rate: float
    subtotal: float
    discount_percent: float = 0
    total_price: float

    # Breakdown
    items: List[Dict[str, Any]]

    # AI recommendations
    priority_order: List[str]
    quick_wins: List[str]
    ai_summary: str


class AuditResponse(BaseModel):
    success: bool
    audit_id: str
    message: str
    status: AuditStatus
