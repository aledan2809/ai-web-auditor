"""
Pydantic models for standalone AIWebAuditor
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AuditCategory(str, Enum):
    SEO = "seo"
    ACCESSIBILITY = "accessibility"
    SECURITY = "security"
    PERFORMANCE = "performance"
    GDPR = "gdpr"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueStatus(str, Enum):
    OPEN = "open"
    FIXED = "fixed"
    PARTIALLY_FIXED = "partially_fixed"
    NOT_FIXED = "not_fixed"


class AuditIssue(BaseModel):
    id: str
    category: AuditCategory
    severity: Severity
    title: str
    description: str
    recommendation: str
    location: Optional[str] = None
    selector: Optional[str] = None
    affected_element: Optional[str] = None
    estimated_hours: float = 1.0
    complexity: str = "medium"


class CategoryScore(BaseModel):
    category: AuditCategory
    score: int = Field(ge=0, le=100)
    issues_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


class AuditReport(BaseModel):
    url: str
    timestamp: str
    overall_score: int = Field(ge=0, le=100)
    category_scores: List[CategoryScore] = []
    issues: List[AuditIssue] = []
    total_issues: int = 0
    issues_by_severity: Dict[str, int] = {}
    metadata: Dict[str, Any] = {}


class FixPatch(BaseModel):
    issue_id: str
    file_path: Optional[str] = None
    original: str
    fixed: str
    diff: str
    description: str
    auto_applicable: bool = False


class FixReport(BaseModel):
    source_audit: str
    timestamp: str
    total_issues: int = 0
    fixable_issues: int = 0
    patches_generated: int = 0
    patches: List[FixPatch] = []
    unfixable_reasons: Dict[str, str] = {}


class RetestComparison(BaseModel):
    issue_id: str
    title: str
    severity: str
    status: IssueStatus
    original_description: str
    retest_description: Optional[str] = None


class RetestReport(BaseModel):
    original_audit: str
    retest_timestamp: str
    url: str
    original_score: int
    retest_score: int
    score_change: int
    total_original_issues: int
    resolved_issues: int
    remaining_issues: int
    new_issues: int
    resolved_percentage: float
    comparisons: List[RetestComparison] = []
    issues: List[AuditIssue] = []
