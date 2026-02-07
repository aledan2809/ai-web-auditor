"""
GDPR Auditor - Checks GDPR compliance, cookies, and privacy
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
import re

from models.schemas import (
    GDPRMetrics, AuditIssue, AuditType, Severity
)
from translations import t


@dataclass
class GDPRResult:
    score: int
    metrics: GDPRMetrics
    issues: List[AuditIssue]


class GDPRAuditor:
    """Audits website GDPR compliance"""

    def __init__(self):
        # Common tracking scripts
        self.tracking_patterns = {
            'google_analytics': [
                r'google-analytics\.com',
                r'googletagmanager\.com',
                r'gtag\(',
                r'ga\(',
                r'UA-\d+-\d+',
                r'G-[A-Z0-9]+'
            ],
            'facebook': [
                r'facebook\.net',
                r'facebook\.com/tr',
                r'fbq\(',
                r'connect\.facebook'
            ],
            'hotjar': [
                r'hotjar\.com',
                r'hj\('
            ],
            'mixpanel': [
                r'mixpanel\.com',
                r'mixpanel\.'
            ],
            'hubspot': [
                r'hubspot\.com',
                r'hs-scripts'
            ],
            'linkedin': [
                r'linkedin\.com/px',
                r'snap\.licdn'
            ],
            'twitter': [
                r'ads-twitter\.com',
                r'twq\('
            ],
            'tiktok': [
                r'tiktok\.com',
                r'ttq\.'
            ]
        }

        # Cookie banner indicators
        self.cookie_banner_patterns = [
            r'cookie[_-]?consent',
            r'cookie[_-]?banner',
            r'cookie[_-]?notice',
            r'gdpr[_-]?consent',
            r'privacy[_-]?banner',
            r'accept[_-]?cookies',
            r'cookiebot',
            r'onetrust',
            r'trustarc',
            r'quantcast',
            r'iubenda'
        ]

    async def audit(self, url: str, lang: str = "ro") -> GDPRResult:
        """Run GDPR compliance audit"""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            content = response.text
            soup = BeautifulSoup(content, 'lxml')

            # Check for cookie banner
            cookie_banner = self._detect_cookie_banner(soup, content)

            # Check for privacy policy link
            privacy_link = self._find_privacy_policy(soup, url)

            # Check cookie consent UI
            consent_ui = self._analyze_consent_ui(soup, content)

            # Find third-party trackers
            trackers = self._find_trackers(content)

            # Check for specific trackers
            has_ga = self._has_tracker(content, self.tracking_patterns['google_analytics'])
            has_fb = self._has_tracker(content, self.tracking_patterns['facebook'])

            # Check for data retention info
            data_retention = self._check_data_retention(soup)

            # Build metrics
            metrics = GDPRMetrics(
                score=0,
                cookie_banner_present=cookie_banner,
                privacy_policy_link=privacy_link is not None,
                cookie_categories_explained=consent_ui.get('categories_explained', False),
                opt_out_option=consent_ui.get('opt_out', False),
                third_party_trackers=trackers,
                google_analytics=has_ga,
                facebook_pixel=has_fb,
                data_retention_info=data_retention
            )

            # Generate issues
            issues = self._generate_issues(metrics, url, trackers, consent_ui, lang)

            # Calculate score
            score = self._calculate_score(metrics)
            metrics.score = score

            return GDPRResult(score=score, metrics=metrics, issues=issues)

    def _detect_cookie_banner(self, soup: BeautifulSoup, content: str) -> bool:
        """Detect if cookie consent banner exists"""
        content_lower = content.lower()

        # Check for common cookie consent patterns
        for pattern in self.cookie_banner_patterns:
            if re.search(pattern, content_lower):
                return True

        # Check for common cookie consent elements
        cookie_elements = soup.find_all(
            ['div', 'section', 'aside'],
            class_=re.compile(r'cookie|consent|gdpr|privacy', re.I)
        )

        return len(cookie_elements) > 0

    def _find_privacy_policy(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find privacy policy link"""
        privacy_patterns = [
            r'privacy[_-]?policy',
            r'politica[_-]?de[_-]?confidentialitate',
            r'gdpr',
            r'data[_-]?protection',
            r'politica[_-]?privind'
        ]

        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()

            for pattern in privacy_patterns:
                if re.search(pattern, href) or re.search(pattern, text):
                    return link['href']

        return None

    def _analyze_consent_ui(self, soup: BeautifulSoup, content: str) -> dict:
        """Analyze cookie consent UI for GDPR compliance"""
        result = {
            'categories_explained': False,
            'opt_out': False,
            'granular_control': False,
            'reject_all': False
        }

        content_lower = content.lower()

        # Check for cookie categories
        category_keywords = [
            'necessary', 'essential', 'functional', 'performance',
            'analytics', 'marketing', 'advertising', 'preferences',
            'necesare', 'functionale', 'analitice', 'publicitate'
        ]

        categories_found = sum(1 for kw in category_keywords if kw in content_lower)
        result['categories_explained'] = categories_found >= 2

        # Check for opt-out/reject options
        reject_patterns = [
            r'reject\s*all',
            r'decline\s*all',
            r'refuse',
            r'opt[_-]?out',
            r'respinge',
            r'refuz'
        ]

        for pattern in reject_patterns:
            if re.search(pattern, content_lower):
                result['opt_out'] = True
                result['reject_all'] = True
                break

        # Check for granular control
        if soup.find_all(['input', 'toggle', 'switch'], class_=re.compile(r'cookie|consent', re.I)):
            result['granular_control'] = True

        return result

    def _find_trackers(self, content: str) -> List[str]:
        """Find all third-party trackers"""
        trackers = []

        for tracker_name, patterns in self.tracking_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.I):
                    if tracker_name not in trackers:
                        trackers.append(tracker_name)
                    break

        return trackers

    def _has_tracker(self, content: str, patterns: List[str]) -> bool:
        """Check if specific tracker exists"""
        for pattern in patterns:
            if re.search(pattern, content, re.I):
                return True
        return False

    def _check_data_retention(self, soup: BeautifulSoup) -> bool:
        """Check for data retention information"""
        retention_patterns = [
            r'data\s*retention',
            r'retention\s*period',
            r'păstrare\s*date',
            r'perioadă\s*de\s*stocare'
        ]

        text = soup.get_text().lower()

        for pattern in retention_patterns:
            if re.search(pattern, text):
                return True

        return False

    def _calculate_score(self, metrics: GDPRMetrics) -> int:
        """Calculate GDPR compliance score"""
        score = 100

        # Cookie banner (-30)
        if not metrics.cookie_banner_present:
            if metrics.third_party_trackers:
                score -= 30
            else:
                score -= 10

        # Privacy policy (-25)
        if not metrics.privacy_policy_link:
            score -= 25

        # Consent UI quality (-20)
        if not metrics.cookie_categories_explained:
            score -= 10
        if not metrics.opt_out_option:
            score -= 10

        # Trackers without consent (-15)
        if metrics.third_party_trackers and not metrics.cookie_banner_present:
            score -= 15

        return max(0, score)

    def _generate_issues(
        self,
        metrics: GDPRMetrics,
        url: str,
        trackers: List[str],
        consent_ui: dict,
        lang: str = "ro"
    ) -> List[AuditIssue]:
        """Generate GDPR compliance issues"""
        issues = []

        # Cookie banner missing
        if not metrics.cookie_banner_present and trackers:
            no_banner_title = "Missing cookie consent banner" if lang == "en" else "Lipseste banner-ul de cookie consent"
            no_banner_desc = f"Site uses {len(trackers)} trackers but has no GDPR consent banner." if lang == "en" else f"Site-ul foloseste {len(trackers)} trackere dar nu are banner de consimtamant GDPR."
            no_banner_rec = "Implement a cookie consent system (e.g., CookieBot, OneTrust) that asks for user consent." if lang == "en" else "Implementati un sistem de cookie consent (ex: CookieBot, OneTrust) care cere acordul utilizatorilor."
            issues.append(AuditIssue(
                id=f"gdpr_no_banner_{hash(url)}",
                category=AuditType.GDPR,
                severity=Severity.CRITICAL,
                title=no_banner_title,
                description=no_banner_desc,
                recommendation=no_banner_rec,
                estimated_hours=8.0,
                complexity="complex"
            ))

        # Privacy policy missing
        if not metrics.privacy_policy_link:
            issues.append(AuditIssue(
                id=f"gdpr_no_privacy_{hash(url)}",
                category=AuditType.GDPR,
                severity=Severity.CRITICAL,
                title=t("gdpr_no_privacy", lang),
                description=t("gdpr_no_privacy_desc", lang),
                recommendation=t("gdpr_no_privacy_rec", lang),
                estimated_hours=4.0,
                complexity="medium"
            ))

        # No cookie categories
        if not metrics.cookie_categories_explained and metrics.cookie_banner_present:
            no_categories_title = "Cookie categories not explained" if lang == "en" else "Categoriile de cookie-uri nu sunt explicate"
            no_categories_desc = "Cookie banner does not provide information about cookie types." if lang == "en" else "Banner-ul de cookie nu ofera informatii despre tipurile de cookie-uri."
            no_categories_rec = "Add cookie categories (Necessary, Functional, Analytics, Marketing) with descriptions." if lang == "en" else "Adaugati categorii de cookie-uri (Necesare, Functionale, Analitice, Marketing) cu descrieri."
            issues.append(AuditIssue(
                id=f"gdpr_no_categories_{hash(url)}",
                category=AuditType.GDPR,
                severity=Severity.HIGH,
                title=no_categories_title,
                description=no_categories_desc,
                recommendation=no_categories_rec,
                estimated_hours=3.0,
                complexity="medium"
            ))

        # No reject/opt-out option
        if not metrics.opt_out_option and metrics.cookie_banner_present:
            no_reject_title = "Missing reject option" if lang == "en" else "Lipseste optiunea de refuz"
            no_reject_desc = "Users cannot reject non-essential cookies." if lang == "en" else "Utilizatorii nu pot refuza cookie-urile non-esentiale."
            no_reject_rec = "Add a 'Reject all' or 'Only necessary' button as visible as 'Accept'." if lang == "en" else "Adaugati un buton 'Refuza toate' sau 'Doar necesare' la fel de vizibil ca 'Accept'."
            issues.append(AuditIssue(
                id=f"gdpr_no_reject_{hash(url)}",
                category=AuditType.GDPR,
                severity=Severity.HIGH,
                title=no_reject_title,
                description=no_reject_desc,
                recommendation=no_reject_rec,
                estimated_hours=2.0,
                complexity="simple"
            ))

        # Third-party trackers
        if trackers:
            tracker_list = ', '.join(trackers)
            trackers_title = f"{len(trackers)} tracking services detected" if lang == "en" else f"{len(trackers)} servicii de tracking detectate"
            trackers_desc = f"Trackers found: {tracker_list}" if lang == "en" else f"Trackere gasite: {tracker_list}"
            trackers_rec = "Document all trackers in the privacy policy and ensure they are loaded only after consent." if lang == "en" else "Documentati toate trackerele in politica de confidentialitate si asigurati-va ca sunt incarcate doar dupa consimtamant."
            issues.append(AuditIssue(
                id=f"gdpr_trackers_{hash(url)}",
                category=AuditType.GDPR,
                severity=Severity.MEDIUM,
                title=trackers_title,
                description=trackers_desc,
                recommendation=trackers_rec,
                estimated_hours=2.0,
                complexity="medium"
            ))

        # Google Analytics without consent
        if metrics.google_analytics and not metrics.cookie_banner_present:
            ga_title = "Google Analytics without consent" if lang == "en" else "Google Analytics fara consimtamant"
            ga_desc = "Google Analytics is loaded before obtaining user consent." if lang == "en" else "Google Analytics este incarcat inainte de a obtine consimtamantul utilizatorului."
            ga_rec = "Configure GA to load only after analytics cookies are accepted." if lang == "en" else "Configurati GA sa se incarce doar dupa acceptarea cookie-urilor de analiza."
            issues.append(AuditIssue(
                id=f"gdpr_ga_no_consent_{hash(url)}",
                category=AuditType.GDPR,
                severity=Severity.HIGH,
                title=ga_title,
                description=ga_desc,
                recommendation=ga_rec,
                estimated_hours=3.0,
                complexity="medium"
            ))

        # Facebook Pixel
        if metrics.facebook_pixel:
            fb_title = "Facebook Pixel detected" if lang == "en" else "Facebook Pixel detectat"
            fb_desc = "Facebook Pixel collects data and requires explicit consent." if lang == "en" else "Facebook Pixel colecteaza date si necesita consimtamant explicit."
            fb_rec = "Ensure FB Pixel is loaded only after consent and is documented in Privacy Policy." if lang == "en" else "Asigurati-va ca FB Pixel se incarca doar dupa consimtamant si este documentat in Privacy Policy."
            issues.append(AuditIssue(
                id=f"gdpr_fb_pixel_{hash(url)}",
                category=AuditType.GDPR,
                severity=Severity.MEDIUM,
                title=fb_title,
                description=fb_desc,
                recommendation=fb_rec,
                estimated_hours=2.0,
                complexity="medium"
            ))

        return issues
