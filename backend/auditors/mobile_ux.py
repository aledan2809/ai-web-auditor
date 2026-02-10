"""
Mobile UX Auditor (MOBUX)
Checks: viewport, intrusive popups, CTA presence, mobile nav, form friction.
Reference: ISSUE_LIBRARY_v1.md §7 (MOBUX-001..005)
"""

from dataclasses import dataclass, field
from typing import List
import httpx
from bs4 import BeautifulSoup

from models.schemas import AuditIssue, AuditType, Severity


@dataclass
class MobileUXResult:
    score: int = 0
    issues: List[AuditIssue] = field(default_factory=list)
    has_viewport: bool = False
    has_intrusive_popup: bool = False
    has_cta_above_fold: bool = False
    mobile_nav_present: bool = False
    form_field_count: int = 0


class MobileUXAuditor:
    """Audits mobile UX factors per ISSUE_LIBRARY_v1.md MOBUX checks."""

    CTA_PATTERNS = [
        "contact", "book", "call", "get started", "sign up", "buy",
        "order", "schedule", "request", "enquire", "free", "demo",
    ]

    POPUP_SELECTORS = [
        "[class*='popup']", "[class*='modal']", "[class*='overlay']",
        "[class*='lightbox']", "[id*='popup']", "[id*='modal']",
    ]

    async def audit(self, url: str, lang: str = "en") -> MobileUXResult:
        result = MobileUXResult()
        issues: List[AuditIssue] = []

        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"},
            ) as client:
                resp = await client.get(url)
                soup = BeautifulSoup(resp.content, "lxml")
        except Exception:
            result.score = 50
            issues.append(AuditIssue(
                id="MOBUX-ERR",
                category=AuditType.UI_UX,
                severity=Severity.MEDIUM,
                title="Could not fetch page for mobile UX analysis",
                description="The page could not be loaded for mobile analysis.",
                recommendation="Ensure the site is accessible.",
                estimated_hours=0,
            ))
            result.issues = issues
            return result

        # MOBUX-VIEWPORT-001
        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        result.has_viewport = viewport_tag is not None
        if not result.has_viewport:
            issues.append(AuditIssue(
                id="MOBUX-VIEWPORT-001",
                category=AuditType.UI_UX,
                severity=Severity.HIGH,
                title="Missing viewport meta tag",
                description="No <meta name='viewport'> found. Mobile layout will not scale correctly.",
                recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1'> to <head>.",
                estimated_hours=0.25,
                complexity="simple",
            ))

        # MOBUX-POPUP-002
        for sel in self.POPUP_SELECTORS:
            if soup.select(sel):
                result.has_intrusive_popup = True
                break
        if result.has_intrusive_popup:
            issues.append(AuditIssue(
                id="MOBUX-POPUP-002",
                category=AuditType.UI_UX,
                severity=Severity.HIGH,
                title="Potential intrusive popup detected",
                description="Popup/modal/overlay elements found that may block content on mobile.",
                recommendation="Delay popups, ensure easy close on mobile, avoid covering primary content on load.",
                estimated_hours=1.5,
                complexity="medium",
            ))

        # MOBUX-CTA-003
        body_text = (soup.body.get_text(" ", strip=True) if soup.body else "").lower()
        links = soup.find_all("a", href=True)
        buttons = soup.find_all("button")
        cta_found = False
        for el in links[:30] + buttons[:10]:
            txt = el.get_text(strip=True).lower()
            if any(p in txt for p in self.CTA_PATTERNS):
                cta_found = True
                break
        result.has_cta_above_fold = cta_found
        if not cta_found:
            issues.append(AuditIssue(
                id="MOBUX-CTA-003",
                category=AuditType.UI_UX,
                severity=Severity.HIGH,
                title="No clear CTA found above the fold",
                description="Could not detect a clear call-to-action button or link in the page content.",
                recommendation="Add a visible CTA (e.g., 'Contact us', 'Book now') in the hero section.",
                estimated_hours=1.0,
                complexity="medium",
            ))

        # MOBUX-NAV-004
        nav = soup.find("nav") or soup.find(attrs={"role": "navigation"})
        hamburger = soup.select("[class*='hamburger'], [class*='menu-toggle'], [class*='mobile-menu'], [aria-label*='menu']")
        result.mobile_nav_present = nav is not None or bool(hamburger)
        if not result.mobile_nav_present:
            issues.append(AuditIssue(
                id="MOBUX-NAV-004",
                category=AuditType.UI_UX,
                severity=Severity.HIGH,
                title="Mobile navigation not detected",
                description="No <nav> element or mobile menu toggle found.",
                recommendation="Implement a responsive navigation menu with hamburger toggle for mobile.",
                estimated_hours=2.0,
                complexity="medium",
            ))

        # MOBUX-FORM-005
        forms = soup.find_all("form")
        max_fields = 0
        for form in forms:
            inputs = form.find_all(["input", "select", "textarea"])
            visible = [i for i in inputs if i.get("type") not in ("hidden", "submit")]
            max_fields = max(max_fields, len(visible))
        result.form_field_count = max_fields
        if max_fields > 6:
            issues.append(AuditIssue(
                id="MOBUX-FORM-005",
                category=AuditType.UI_UX,
                severity=Severity.MEDIUM,
                title="Forms have too many fields",
                description=f"A form with {max_fields} visible fields was detected. Long forms increase mobile friction.",
                recommendation="Reduce to essential fields (name, email, message). Make phone optional.",
                estimated_hours=1.0,
                complexity="medium",
            ))

        # Score
        deductions = 0
        if not result.has_viewport:
            deductions += 25
        if result.has_intrusive_popup:
            deductions += 20
        if not cta_found:
            deductions += 20
        if not result.mobile_nav_present:
            deductions += 20
        if max_fields > 6:
            deductions += 15

        result.score = max(0, 100 - deductions)
        result.issues = issues
        return result
