"""
Competitor Gap Auditor (COMP)
Compares audited site against a competitor on key metrics.
Reference: COMPETITOR_POLICY_v1.md, ISSUE_LIBRARY_v1.md §9
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import httpx
from bs4 import BeautifulSoup
import re

from models.schemas import AuditIssue, AuditType, Severity


@dataclass
class CompetitorMetrics:
    url: str = ""
    has_h1: bool = False
    title_length: int = 0
    meta_desc_length: int = 0
    has_viewport: bool = False
    has_https: bool = False
    has_contact: bool = False
    has_social_proof: bool = False
    load_time_ms: float = 0


@dataclass
class CompetitorResult:
    score: int = 0
    issues: List[AuditIssue] = field(default_factory=list)
    confidence: float = 0.0
    competitor_url: Optional[str] = None
    competitor_metrics: Optional[CompetitorMetrics] = None
    site_metrics: Optional[CompetitorMetrics] = None
    advantages: List[Dict] = field(default_factory=list)
    quick_wins: List[Dict] = field(default_factory=list)


class CompetitorAuditor:
    """
    Compares the audited site against a competitor.
    v1: basic comparison on SEO hygiene, mobile, trust.
    Reference: COMPETITOR_POLICY_v1.md §4
    """

    PHONE_REGEX = re.compile(r"\+?\d[\d\s\-().]{7,}\d")

    async def audit(
        self,
        url: str,
        competitor_url: Optional[str] = None,
        lang: str = "en",
    ) -> CompetitorResult:
        result = CompetitorResult()

        if not competitor_url:
            # No competitor provided — gap disabled
            result.confidence = 0.0
            result.score = 50  # neutral
            result.issues.append(AuditIssue(
                id="COMP-IDENT-001",
                category=AuditType.FULL,
                severity=Severity.MEDIUM,
                title="No competitor selected",
                description="Competitor comparison requires a competitor URL. None was provided or auto-detected.",
                recommendation="Provide a competitor URL to enable gap analysis.",
                estimated_hours=0,
                complexity="simple",
            ))
            return result

        # Fetch both sites
        site_metrics = await self._fetch_metrics(url)
        comp_metrics = await self._fetch_metrics(competitor_url)

        result.competitor_url = competitor_url
        result.site_metrics = site_metrics
        result.competitor_metrics = comp_metrics

        # Determine confidence
        if comp_metrics.url:
            result.confidence = 0.75
        else:
            result.confidence = 0.4
            result.score = 50
            result.issues.append(AuditIssue(
                id="COMP-IDENT-001",
                category=AuditType.FULL,
                severity=Severity.MEDIUM,
                title="Competitor analysis limited",
                description="Could not fully access competitor site. Results may be incomplete.",
                recommendation="Verify competitor URL is correct and publicly accessible.",
                estimated_hours=0,
            ))
            return result

        # Compare and generate advantages + issues
        advantages = []
        issues = []

        # H1 comparison
        if comp_metrics.has_h1 and not site_metrics.has_h1:
            advantages.append({"metric": "H1 heading", "competitor": "Present", "you": "Missing", "issueId": "OPSEO-H1-001"})

        # Title comparison
        if 30 <= comp_metrics.title_length <= 60 and not (30 <= site_metrics.title_length <= 60):
            advantages.append({"metric": "Title tag", "competitor": f"{comp_metrics.title_length} chars (good)", "you": f"{site_metrics.title_length} chars", "issueId": "OPSEO-TITLE-003"})

        # Meta description
        if 120 <= comp_metrics.meta_desc_length <= 160 and not (120 <= site_metrics.meta_desc_length <= 160):
            advantages.append({"metric": "Meta description", "competitor": f"{comp_metrics.meta_desc_length} chars (good)", "you": f"{site_metrics.meta_desc_length} chars", "issueId": "OPSEO-META-004"})

        # Viewport
        if comp_metrics.has_viewport and not site_metrics.has_viewport:
            advantages.append({"metric": "Mobile viewport", "competitor": "Present", "you": "Missing", "issueId": "MOBUX-VIEWPORT-001"})

        # Contact
        if comp_metrics.has_contact and not site_metrics.has_contact:
            advantages.append({"metric": "Contact info", "competitor": "Visible", "you": "Not found", "issueId": "TRUST-CONTACT-001"})

        # Social proof
        if comp_metrics.has_social_proof and not site_metrics.has_social_proof:
            advantages.append({"metric": "Social proof", "competitor": "Present", "you": "Missing", "issueId": "TRUST-PROOF-003"})

        result.advantages = advantages[:3]

        # COMP-GAP-002
        if advantages:
            issues.append(AuditIssue(
                id="COMP-GAP-002",
                category=AuditType.FULL,
                severity=Severity.HIGH,
                title=f"Competitor outperforms you in {len(advantages)} area(s)",
                description="Your competitor has advantages in: " + ", ".join(a["metric"] for a in advantages[:3]) + ".",
                recommendation="Fix the mapped issues to close the gap.",
                estimated_hours=0,
                complexity="medium",
            ))

        # Quick wins: issues from advantages that are fixable
        result.quick_wins = [
            {"issueId": a["issueId"], "metric": a["metric"]}
            for a in advantages
            if a.get("issueId")
        ][:3]

        # Score: base 70, +10 for each area where you match/beat competitor
        comparison_areas = 6
        wins = comparison_areas - len(advantages)
        result.score = min(100, max(0, int(70 + (wins / comparison_areas) * 30)))
        result.issues = issues
        return result

    async def _fetch_metrics(self, url: str) -> CompetitorMetrics:
        metrics = CompetitorMetrics(url=url)
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                resp = await client.get(url)
                metrics.load_time_ms = resp.elapsed.total_seconds() * 1000
                soup = BeautifulSoup(resp.content, "lxml")

                metrics.has_https = url.startswith("https://") or str(resp.url).startswith("https://")

                h1 = soup.find("h1")
                metrics.has_h1 = h1 is not None

                title = soup.find("title")
                metrics.title_length = len(title.get_text(strip=True)) if title else 0

                meta = soup.find("meta", attrs={"name": "description"})
                metrics.meta_desc_length = len(meta.get("content", "")) if meta else 0

                viewport = soup.find("meta", attrs={"name": "viewport"})
                metrics.has_viewport = viewport is not None

                body_text = soup.body.get_text(" ", strip=True) if soup.body else ""
                metrics.has_contact = bool(self.PHONE_REGEX.search(body_text))

                proof_kw = ["testimonial", "review", "client", "trusted"]
                metrics.has_social_proof = any(kw in body_text.lower() for kw in proof_kw)

        except Exception:
            metrics.url = ""  # signal failure
        return metrics
