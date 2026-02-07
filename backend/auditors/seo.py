"""
SEO Auditor - Analyzes on-page SEO factors
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

from models.schemas import (
    SEOMetrics, AuditIssue, AuditType, Severity
)
from translations import t


@dataclass
class SEOResult:
    score: int
    metrics: SEOMetrics
    issues: List[AuditIssue]


class SEOAuditor:
    """Audits website SEO factors"""

    def __init__(self):
        self.ideal_title_length = (50, 60)
        self.ideal_description_length = (150, 160)

    async def audit(self, url: str, lang: str = "ro") -> SEOResult:
        """Run SEO audit on URL"""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Fetch main page
            response = await client.get(url)
            soup = BeautifulSoup(response.content, 'lxml')

            # Parse URL for domain
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Extract SEO data
            title = self._get_title(soup)
            meta_desc = self._get_meta_description(soup)
            h1_texts = self._get_h1_texts(soup)
            canonical = self._get_canonical(soup)
            structured_data = self._get_structured_data(soup)
            images_without_alt = self._count_images_without_alt(soup)

            # Check external resources
            robots_exists = await self._check_robots_txt(client, base_url)
            sitemap_exists = await self._check_sitemap(client, base_url)
            broken_links = await self._check_broken_links(client, soup, base_url)

            # Build metrics
            metrics = SEOMetrics(
                score=0,
                title=title,
                title_length=len(title) if title else 0,
                meta_description=meta_desc,
                meta_description_length=len(meta_desc) if meta_desc else 0,
                h1_count=len(h1_texts),
                h1_texts=h1_texts,
                canonical_url=canonical,
                robots_txt_exists=robots_exists,
                sitemap_exists=sitemap_exists,
                structured_data=structured_data,
                broken_links=broken_links[:10],  # Limit to 10
                image_alt_missing=images_without_alt
            )

            # Generate issues
            issues = self._generate_issues(metrics, url, lang)

            # Calculate score
            score = self._calculate_score(metrics)
            metrics.score = score

            return SEOResult(score=score, metrics=metrics, issues=issues)

    def _get_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else None

    def _get_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description"""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', '').strip() if meta else None

    def _get_h1_texts(self, soup: BeautifulSoup) -> List[str]:
        """Extract all H1 texts"""
        h1_tags = soup.find_all('h1')
        return [h1.get_text().strip() for h1 in h1_tags]

    def _get_canonical(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract canonical URL"""
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        return canonical.get('href') if canonical else None

    def _get_structured_data(self, soup: BeautifulSoup) -> List[str]:
        """Extract structured data types"""
        schemas = []
        script_tags = soup.find_all('script', attrs={'type': 'application/ld+json'})
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    schemas.append(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            schemas.append(item['@type'])
            except Exception:
                pass
        return schemas

    def _count_images_without_alt(self, soup: BeautifulSoup) -> int:
        """Count images without alt attribute"""
        images = soup.find_all('img')
        return sum(1 for img in images if not img.get('alt'))

    async def _check_robots_txt(self, client: httpx.AsyncClient, base_url: str) -> bool:
        """Check if robots.txt exists"""
        try:
            response = await client.get(f"{base_url}/robots.txt")
            return response.status_code == 200
        except Exception:
            return False

    async def _check_sitemap(self, client: httpx.AsyncClient, base_url: str) -> bool:
        """Check if sitemap.xml exists"""
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemap/"
        ]
        for url in sitemap_urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
        return False

    async def _check_broken_links(
        self,
        client: httpx.AsyncClient,
        soup: BeautifulSoup,
        base_url: str
    ) -> List[str]:
        """Check for broken links (limited check)"""
        broken = []
        links = soup.find_all('a', href=True)

        # Check only first 20 internal links
        internal_links = [
            urljoin(base_url, link['href'])
            for link in links[:30]
            if link['href'].startswith('/') or base_url in link['href']
        ]

        for link in internal_links[:20]:
            try:
                response = await client.head(link, timeout=5.0)
                if response.status_code >= 400:
                    broken.append(link)
            except Exception:
                broken.append(link)

        return broken

    def _calculate_score(self, metrics: SEOMetrics) -> int:
        """Calculate SEO score"""
        score = 100

        # Title checks (-15 max)
        if not metrics.title:
            score -= 15
        elif metrics.title_length < self.ideal_title_length[0]:
            score -= 5
        elif metrics.title_length > self.ideal_title_length[1]:
            score -= 5

        # Meta description checks (-15 max)
        if not metrics.meta_description:
            score -= 15
        elif metrics.meta_description_length < self.ideal_description_length[0]:
            score -= 5
        elif metrics.meta_description_length > self.ideal_description_length[1]:
            score -= 5

        # H1 checks (-10 max)
        if metrics.h1_count == 0:
            score -= 10
        elif metrics.h1_count > 1:
            score -= 5

        # Technical SEO (-20 max)
        if not metrics.robots_txt_exists:
            score -= 5
        if not metrics.sitemap_exists:
            score -= 10
        if not metrics.canonical_url:
            score -= 5

        # Broken links (-15 max)
        broken_count = len(metrics.broken_links)
        if broken_count > 0:
            score -= min(15, broken_count * 3)

        # Images without alt (-10 max)
        if metrics.image_alt_missing > 0:
            score -= min(10, metrics.image_alt_missing)

        # Structured data bonus (+5)
        if metrics.structured_data:
            score = min(100, score + 5)

        return max(0, score)

    def _generate_issues(self, metrics: SEOMetrics, url: str, lang: str = "ro") -> List[AuditIssue]:
        """Generate SEO issues"""
        issues = []

        # Title issues
        if not metrics.title:
            issues.append(AuditIssue(
                id=f"seo_no_title_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.CRITICAL,
                title=t("seo_no_title", lang),
                description=t("seo_no_title_desc", lang),
                recommendation=t("seo_no_title_rec", lang),
                estimated_hours=0.5,
                complexity="simple"
            ))
        elif metrics.title_length < self.ideal_title_length[0]:
            issues.append(AuditIssue(
                id=f"seo_short_title_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.MEDIUM,
                title=t("seo_short_title", lang),
                description=t("seo_short_title_desc", lang, metrics.title_length, self.ideal_title_length[0], self.ideal_title_length[1]),
                recommendation=t("seo_short_title_rec", lang),
                estimated_hours=0.5,
                complexity="simple"
            ))
        elif metrics.title_length > 70:
            issues.append(AuditIssue(
                id=f"seo_long_title_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.LOW,
                title=t("seo_long_title", lang),
                description=t("seo_long_title_desc", lang, metrics.title_length),
                recommendation=t("seo_long_title_rec", lang),
                estimated_hours=0.5,
                complexity="simple"
            ))

        # Meta description issues
        if not metrics.meta_description:
            issues.append(AuditIssue(
                id=f"seo_no_meta_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.HIGH,
                title=t("seo_no_meta", lang),
                description=t("seo_no_meta_desc", lang),
                recommendation=t("seo_no_meta_rec", lang),
                estimated_hours=0.5,
                complexity="simple"
            ))

        # H1 issues
        if metrics.h1_count == 0:
            issues.append(AuditIssue(
                id=f"seo_no_h1_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.HIGH,
                title=t("seo_no_h1", lang),
                description=t("seo_no_h1_desc", lang),
                recommendation=t("seo_no_h1_rec", lang),
                estimated_hours=0.5,
                complexity="simple"
            ))
        elif metrics.h1_count > 1:
            issues.append(AuditIssue(
                id=f"seo_multiple_h1_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.MEDIUM,
                title=t("seo_multiple_h1", lang),
                description=t("seo_multiple_h1_desc", lang, metrics.h1_count),
                recommendation=t("seo_multiple_h1_rec", lang),
                estimated_hours=1.0,
                complexity="simple"
            ))

        # Technical SEO issues
        if not metrics.robots_txt_exists:
            issues.append(AuditIssue(
                id=f"seo_no_robots_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.MEDIUM,
                title=t("seo_no_robots", lang),
                description=t("seo_no_robots_desc", lang),
                recommendation=t("seo_no_robots_rec", lang),
                estimated_hours=1.0,
                complexity="simple"
            ))

        if not metrics.sitemap_exists:
            issues.append(AuditIssue(
                id=f"seo_no_sitemap_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.HIGH,
                title=t("seo_no_sitemap", lang),
                description=t("seo_no_sitemap_desc", lang),
                recommendation=t("seo_no_sitemap_rec", lang),
                estimated_hours=2.0,
                complexity="medium"
            ))

        # Broken links
        if metrics.broken_links:
            issues.append(AuditIssue(
                id=f"seo_broken_links_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.HIGH,
                title=t("seo_broken_links", lang, len(metrics.broken_links)),
                description=t("seo_broken_links_desc", lang, ', '.join(metrics.broken_links[:5])),
                recommendation=t("seo_broken_links_rec", lang),
                estimated_hours=len(metrics.broken_links) * 0.25,
                complexity="simple"
            ))

        # Images without alt
        if metrics.image_alt_missing > 0:
            issues.append(AuditIssue(
                id=f"seo_missing_alt_{hash(url)}",
                category=AuditType.SEO,
                severity=Severity.MEDIUM,
                title=t("seo_missing_alt", lang, metrics.image_alt_missing),
                description=t("seo_missing_alt_desc", lang),
                recommendation=t("seo_missing_alt_rec", lang),
                estimated_hours=metrics.image_alt_missing * 0.1,
                complexity="simple"
            ))

        return issues
