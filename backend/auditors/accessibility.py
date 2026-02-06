"""
Accessibility Auditor - Checks WCAG 2.1 compliance
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
import re

from models.schemas import (
    AccessibilityMetrics, AuditIssue, AuditType, Severity
)


@dataclass
class AccessibilityResult:
    score: int
    metrics: AccessibilityMetrics
    issues: List[AuditIssue]


class AccessibilityAuditor:
    """Audits website accessibility (WCAG 2.1)"""

    def __init__(self):
        pass

    async def audit(self, url: str) -> AccessibilityResult:
        """Run accessibility audit"""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.content, 'lxml')

            # Check various accessibility criteria
            missing_alt = self._check_image_alts(soup)
            missing_labels = self._check_form_labels(soup)
            heading_issues = self._check_heading_hierarchy(soup)
            contrast_issues = self._estimate_contrast_issues(soup)
            aria_usage = self._count_aria_usage(soup)
            keyboard_nav = self._check_keyboard_navigation(soup)
            lang_attr = self._check_language_attribute(soup)
            skip_links = self._check_skip_links(soup)

            # Determine WCAG level
            wcag_level = self._determine_wcag_level(
                missing_alt, missing_labels, heading_issues, lang_attr
            )

            # Build metrics
            metrics = AccessibilityMetrics(
                score=0,
                wcag_level=wcag_level,
                color_contrast_issues=contrast_issues,
                missing_alt_texts=missing_alt,
                missing_form_labels=missing_labels,
                keyboard_navigation=keyboard_nav,
                aria_usage=aria_usage,
                heading_hierarchy_valid=len(heading_issues) == 0
            )

            # Generate issues
            issues = self._generate_issues(
                metrics, url, soup, heading_issues, lang_attr, skip_links
            )

            # Calculate score
            score = self._calculate_score(metrics, lang_attr, skip_links)
            metrics.score = score

            return AccessibilityResult(score=score, metrics=metrics, issues=issues)

    def _check_image_alts(self, soup: BeautifulSoup) -> int:
        """Count images without alt text"""
        images = soup.find_all('img')
        missing = 0

        for img in images:
            alt = img.get('alt')
            # alt="" is valid for decorative images
            if alt is None:
                missing += 1

        return missing

    def _check_form_labels(self, soup: BeautifulSoup) -> int:
        """Count form inputs without labels"""
        inputs = soup.find_all(['input', 'select', 'textarea'])
        missing = 0

        for inp in inputs:
            inp_type = inp.get('type', 'text')
            # Skip hidden, submit, button, image inputs
            if inp_type in ['hidden', 'submit', 'button', 'image', 'reset']:
                continue

            inp_id = inp.get('id')
            has_label = False

            # Check for associated label
            if inp_id:
                label = soup.find('label', attrs={'for': inp_id})
                if label:
                    has_label = True

            # Check for aria-label or aria-labelledby
            if inp.get('aria-label') or inp.get('aria-labelledby'):
                has_label = True

            # Check for wrapping label
            parent = inp.find_parent('label')
            if parent:
                has_label = True

            # Check for placeholder (not ideal but counts)
            if inp.get('placeholder'):
                has_label = True

            if not has_label:
                missing += 1

        return missing

    def _check_heading_hierarchy(self, soup: BeautifulSoup) -> List[str]:
        """Check for heading hierarchy issues"""
        issues = []
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        if not headings:
            issues.append("No headings found")
            return issues

        # Check for h1
        h1_count = len(soup.find_all('h1'))
        if h1_count == 0:
            issues.append("Missing H1 heading")
        elif h1_count > 1:
            issues.append(f"Multiple H1 headings ({h1_count})")

        # Check hierarchy (no skipping levels)
        prev_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if level > prev_level + 1 and prev_level > 0:
                issues.append(f"Skipped heading level: H{prev_level} to H{level}")
            prev_level = level

        return issues

    def _estimate_contrast_issues(self, soup: BeautifulSoup) -> int:
        """Estimate color contrast issues (simplified check)"""
        # Real contrast checking requires CSS computation
        # This is a simplified heuristic

        issues = 0

        # Check for common low-contrast patterns
        style_elements = soup.find_all(style=True)

        for elem in style_elements:
            style = elem.get('style', '').lower()

            # Check for light gray text
            if 'color:' in style:
                if any(c in style for c in ['#ccc', '#ddd', '#eee', '#999', 'lightgray', 'silver']):
                    issues += 1

        # Check for text on images without overlay
        text_on_images = soup.find_all(['div', 'section'], class_=re.compile(r'hero|banner|header', re.I))
        issues += len(text_on_images)  # Potential issues

        return min(issues, 10)  # Cap at 10

    def _count_aria_usage(self, soup: BeautifulSoup) -> int:
        """Count ARIA attributes usage"""
        aria_attrs = ['aria-label', 'aria-labelledby', 'aria-describedby',
                      'aria-hidden', 'aria-live', 'aria-expanded', 'role']

        count = 0
        for attr in aria_attrs:
            elements = soup.find_all(attrs={attr: True})
            count += len(elements)

        return count

    def _check_keyboard_navigation(self, soup: BeautifulSoup) -> bool:
        """Check for keyboard navigation support"""
        # Check for tabindex usage
        tabindex_elements = soup.find_all(attrs={'tabindex': True})

        # Check for focus styles (heuristic)
        style_tags = soup.find_all('style')
        has_focus_styles = any(':focus' in str(style) for style in style_tags)

        # Check for skip links
        skip_link = soup.find('a', href='#main') or soup.find('a', href='#content')

        return len(tabindex_elements) > 0 or has_focus_styles or skip_link is not None

    def _check_language_attribute(self, soup: BeautifulSoup) -> bool:
        """Check for lang attribute on html element"""
        html = soup.find('html')
        return html is not None and html.get('lang') is not None

    def _check_skip_links(self, soup: BeautifulSoup) -> bool:
        """Check for skip navigation links"""
        skip_patterns = ['#main', '#content', '#skip', 'skip-nav', 'skip-link']

        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()

            for pattern in skip_patterns:
                if pattern in href or 'skip' in text:
                    return True

        return False

    def _determine_wcag_level(
        self,
        missing_alt: int,
        missing_labels: int,
        heading_issues: List[str],
        has_lang: bool
    ) -> str:
        """Determine WCAG compliance level"""
        # Level A requirements
        level_a_pass = (
            missing_alt == 0 and
            missing_labels == 0 and
            has_lang
        )

        # Level AA requirements (includes A + more)
        level_aa_pass = level_a_pass and len(heading_issues) <= 1

        if level_aa_pass:
            return "AA"
        elif level_a_pass:
            return "A"
        else:
            return "Non-compliant"

    def _calculate_score(
        self,
        metrics: AccessibilityMetrics,
        has_lang: bool,
        has_skip: bool
    ) -> int:
        """Calculate accessibility score"""
        score = 100

        # Missing alt texts (-3 each, max -20)
        score -= min(20, metrics.missing_alt_texts * 3)

        # Missing form labels (-5 each, max -15)
        score -= min(15, metrics.missing_form_labels * 5)

        # Heading hierarchy (-10)
        if not metrics.heading_hierarchy_valid:
            score -= 10

        # Contrast issues (-2 each, max -15)
        score -= min(15, metrics.color_contrast_issues * 2)

        # Language attribute (-10)
        if not has_lang:
            score -= 10

        # Skip links (-5)
        if not has_skip:
            score -= 5

        # Keyboard navigation (-10)
        if not metrics.keyboard_navigation:
            score -= 10

        # ARIA usage bonus (+5)
        if metrics.aria_usage >= 5:
            score = min(100, score + 5)

        return max(0, score)

    def _generate_issues(
        self,
        metrics: AccessibilityMetrics,
        url: str,
        soup: BeautifulSoup,
        heading_issues: List[str],
        has_lang: bool,
        has_skip: bool
    ) -> List[AuditIssue]:
        """Generate accessibility issues"""
        issues = []

        # Missing alt texts
        if metrics.missing_alt_texts > 0:
            issues.append(AuditIssue(
                id=f"a11y_missing_alt_{hash(url)}",
                category=AuditType.ACCESSIBILITY,
                severity=Severity.HIGH,
                title=f"{metrics.missing_alt_texts} imagini fără text alternativ",
                description="Imaginile fără atribut alt nu sunt accesibile pentru screen readers.",
                recommendation="Adăugați text alt descriptiv pentru toate imaginile informative. Folosiți alt=\"\" pentru imagini decorative.",
                estimated_hours=metrics.missing_alt_texts * 0.1,
                complexity="simple"
            ))

        # Missing form labels
        if metrics.missing_form_labels > 0:
            issues.append(AuditIssue(
                id=f"a11y_missing_labels_{hash(url)}",
                category=AuditType.ACCESSIBILITY,
                severity=Severity.HIGH,
                title=f"{metrics.missing_form_labels} câmpuri de formular fără label",
                description="Câmpurile fără label nu sunt accesibile pentru utilizatorii de screen reader.",
                recommendation="Adăugați elemente <label> asociate cu fiecare input folosind atributul 'for'.",
                estimated_hours=metrics.missing_form_labels * 0.2,
                complexity="simple"
            ))

        # Heading hierarchy
        for issue in heading_issues:
            severity = Severity.HIGH if "Missing H1" in issue else Severity.MEDIUM
            issues.append(AuditIssue(
                id=f"a11y_heading_{hash(url)}_{hash(issue)}",
                category=AuditType.ACCESSIBILITY,
                severity=severity,
                title=f"Problemă ierarhie heading-uri: {issue}",
                description="Ierarhia de heading-uri trebuie să fie logică și fără salturi.",
                recommendation="Restructurați heading-urile pentru a urma o ierarhie logică (H1 > H2 > H3).",
                estimated_hours=1.0,
                complexity="simple"
            ))

        # Language attribute
        if not has_lang:
            issues.append(AuditIssue(
                id=f"a11y_no_lang_{hash(url)}",
                category=AuditType.ACCESSIBILITY,
                severity=Severity.HIGH,
                title="Lipsește atributul lang pe <html>",
                description="Screen reader-ele nu pot determina limba paginii.",
                recommendation="Adăugați lang=\"ro\" (sau limba corespunzătoare) pe elementul <html>.",
                estimated_hours=0.25,
                complexity="simple"
            ))

        # Skip links
        if not has_skip:
            issues.append(AuditIssue(
                id=f"a11y_no_skip_{hash(url)}",
                category=AuditType.ACCESSIBILITY,
                severity=Severity.MEDIUM,
                title="Lipsesc link-urile skip navigation",
                description="Utilizatorii de tastatură nu pot sări peste navigație.",
                recommendation="Adăugați un link 'Skip to main content' la începutul paginii.",
                estimated_hours=1.0,
                complexity="simple"
            ))

        # Keyboard navigation
        if not metrics.keyboard_navigation:
            issues.append(AuditIssue(
                id=f"a11y_keyboard_{hash(url)}",
                category=AuditType.ACCESSIBILITY,
                severity=Severity.HIGH,
                title="Navigare prin tastatură limitată",
                description="Elementele interactive pot să nu fie accesibile prin tastatură.",
                recommendation="Asigurați-vă că toate elementele interactive au focus visible și sunt accesibile prin Tab.",
                estimated_hours=4.0,
                complexity="medium"
            ))

        # Color contrast
        if metrics.color_contrast_issues > 0:
            issues.append(AuditIssue(
                id=f"a11y_contrast_{hash(url)}",
                category=AuditType.ACCESSIBILITY,
                severity=Severity.MEDIUM,
                title=f"Posibile probleme de contrast ({metrics.color_contrast_issues})",
                description="Text cu contrast insuficient poate fi greu de citit.",
                recommendation="Verificați contrastul culorilor folosind un tool precum WebAIM Contrast Checker. Raportul minim recomandat: 4.5:1.",
                estimated_hours=2.0,
                complexity="medium"
            ))

        # WCAG level
        if metrics.wcag_level == "Non-compliant":
            issues.append(AuditIssue(
                id=f"a11y_wcag_{hash(url)}",
                category=AuditType.ACCESSIBILITY,
                severity=Severity.CRITICAL,
                title="Site-ul nu este conform WCAG 2.1 Level A",
                description="Site-ul nu îndeplinește cerințele minime de accesibilitate.",
                recommendation="Prioritizați rezolvarea problemelor critice pentru a atinge conformitatea WCAG 2.1 Level A.",
                estimated_hours=20.0,
                complexity="complex"
            ))

        return issues
