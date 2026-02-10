"""
Trust & Conversions Auditor (TRUST)
Checks: contact info, about page, social proof, policy links.
Reference: ISSUE_LIBRARY_v1.md §8 (TRUST-001..004)
"""

from dataclasses import dataclass, field
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from models.schemas import AuditIssue, AuditType, Severity


@dataclass
class TrustResult:
    score: int = 0
    issues: List[AuditIssue] = field(default_factory=list)
    has_phone: bool = False
    has_email: bool = False
    has_address: bool = False
    has_about: bool = False
    has_social_proof: bool = False
    has_policy_links: bool = False


class TrustAuditor:
    """Audits trust signals and local presence per ISSUE_LIBRARY_v1.md TRUST checks."""

    PHONE_REGEX = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

    PROOF_PATTERNS = [
        "testimonial", "review", "rating", "client", "customer",
        "case study", "portfolio", "success", "trusted by",
    ]

    POLICY_SLUGS = [
        "privacy", "terms", "cookie", "policy", "legal",
        "politica", "confidentialitate", "termeni",
    ]

    ABOUT_SLUGS = ["about", "about-us", "despre", "despre-noi", "who-we-are"]
    CONTACT_SLUGS = ["contact", "contact-us", "contacteaza"]

    async def audit(self, url: str, lang: str = "en") -> TrustResult:
        result = TrustResult()
        issues: List[AuditIssue] = []

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url)
                soup = BeautifulSoup(resp.content, "lxml")
                body_text = soup.body.get_text(" ", strip=True) if soup.body else ""
                all_links = soup.find_all("a", href=True)
                hrefs = [a.get("href", "") for a in all_links]
                href_text = " ".join(hrefs).lower()
                link_texts = " ".join(a.get_text(strip=True) for a in all_links).lower()
        except Exception:
            result.score = 50
            issues.append(AuditIssue(
                id="TRUST-ERR",
                category=AuditType.UI_UX,
                severity=Severity.MEDIUM,
                title="Could not fetch page for trust analysis",
                description="The page could not be loaded.",
                recommendation="Ensure the site is accessible.",
                estimated_hours=0,
            ))
            result.issues = issues
            return result

        # TRUST-CONTACT-001 — Missing key contact info
        phones = self.PHONE_REGEX.findall(body_text)
        emails = self.EMAIL_REGEX.findall(body_text)
        result.has_phone = len(phones) > 0
        result.has_email = len(emails) > 0

        address_hints = ["street", "road", "floor", "building", "p.o. box",
                         "dubai", "abu dhabi", "sharjah", "ajman", "meydan"]
        result.has_address = any(h in body_text.lower() for h in address_hints)

        missing_contact = []
        if not result.has_phone:
            missing_contact.append("phone")
        if not result.has_email:
            missing_contact.append("email")
        if not result.has_address:
            missing_contact.append("address")

        if missing_contact:
            issues.append(AuditIssue(
                id="TRUST-CONTACT-001",
                category=AuditType.UI_UX,
                severity=Severity.HIGH,
                title="Missing key contact info",
                description=f"Missing: {', '.join(missing_contact)}. Visitors need visible contact details to trust the site.",
                recommendation="Add clickable phone, email, and physical address to header/footer or a contact page.",
                estimated_hours=0.5,
                complexity="simple",
            ))

        # TRUST-ABOUT-002 — Weak About / legitimacy signals
        has_about_link = any(
            any(slug in h.lower() for slug in self.ABOUT_SLUGS)
            for h in hrefs
        )
        result.has_about = has_about_link
        if not has_about_link:
            issues.append(AuditIssue(
                id="TRUST-ABOUT-002",
                category=AuditType.UI_UX,
                severity=Severity.MEDIUM,
                title='Weak "About" / legitimacy signals',
                description="No About Us page link detected in navigation or footer.",
                recommendation="Add an About page with company story, team info, and proof points.",
                estimated_hours=1.0,
                complexity="simple",
            ))

        # TRUST-PROOF-003 — No social proof
        text_lower = body_text.lower()
        result.has_social_proof = any(p in text_lower for p in self.PROOF_PATTERNS)
        if not result.has_social_proof:
            issues.append(AuditIssue(
                id="TRUST-PROOF-003",
                category=AuditType.UI_UX,
                severity=Severity.MEDIUM,
                title="No social proof detected",
                description="No testimonials, reviews, ratings, or case study sections found.",
                recommendation="Add testimonials, client logos, review badges, or case study snippets.",
                estimated_hours=2.0,
                complexity="medium",
            ))

        # TRUST-POLICIES-004 — Footer missing policy links
        footer = soup.find("footer")
        footer_text = footer.get_text(" ", strip=True).lower() if footer else ""
        footer_hrefs = " ".join(a.get("href", "") for a in (footer.find_all("a", href=True) if footer else [])).lower()

        policy_found = any(slug in footer_hrefs or slug in footer_text for slug in self.POLICY_SLUGS)
        result.has_policy_links = policy_found
        if not policy_found:
            issues.append(AuditIssue(
                id="TRUST-POLICIES-004",
                category=AuditType.UI_UX,
                severity=Severity.HIGH,
                title="Footer missing policy links",
                description="No Privacy Policy or Terms links found in the footer.",
                recommendation="Add Privacy Policy and Terms & Conditions links to the footer.",
                estimated_hours=0.5,
                complexity="simple",
            ))

        # Score
        deductions = 0
        if missing_contact:
            deductions += 10 * len(missing_contact)
        if not has_about_link:
            deductions += 15
        if not result.has_social_proof:
            deductions += 15
        if not policy_found:
            deductions += 20

        result.score = max(0, 100 - deductions)
        result.issues = issues
        return result
