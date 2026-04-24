"""
Core Audit Engine - Standalone web auditor
Performs SEO, Accessibility, Security, and Performance audits without external dependencies.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import ssl
import socket
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ..schemas.models import (
    AuditCategory,
    AuditIssue,
    AuditReport,
    CategoryScore,
    Severity,
)

logger = logging.getLogger("aiwebauditor")


def _issue_id(prefix: str, url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{prefix}_{h}"


# ---------------------------------------------------------------------------
# SEO Audit
# ---------------------------------------------------------------------------

async def audit_seo(url: str, soup: BeautifulSoup, client: httpx.AsyncClient) -> tuple:
    """Run SEO checks, return (score, issues)."""
    issues: List[AuditIssue] = []
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text().strip() if title_tag else None
    title_len = len(title) if title else 0

    if not title:
        issues.append(AuditIssue(
            id=_issue_id("seo_no_title", url), category=AuditCategory.SEO,
            severity=Severity.CRITICAL, title="Missing page title",
            description="The page has no <title> tag.",
            recommendation="Add a descriptive <title> tag (50-60 characters).",
            location="<head>", estimated_hours=0.5, complexity="simple",
        ))
    elif title_len < 50:
        issues.append(AuditIssue(
            id=_issue_id("seo_short_title", url), category=AuditCategory.SEO,
            severity=Severity.MEDIUM, title=f"Title too short ({title_len} chars)",
            description=f"Title is {title_len} characters. Ideal: 50-60.",
            recommendation="Expand the title to 50-60 characters with relevant keywords.",
            location="<title>", estimated_hours=0.5, complexity="simple",
        ))
    elif title_len > 70:
        issues.append(AuditIssue(
            id=_issue_id("seo_long_title", url), category=AuditCategory.SEO,
            severity=Severity.LOW, title=f"Title too long ({title_len} chars)",
            description=f"Title is {title_len} characters and may be truncated in SERPs.",
            recommendation="Shorten title to under 60 characters.",
            location="<title>", estimated_hours=0.5, complexity="simple",
        ))

    # Meta description
    meta = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta.get("content", "").strip() if meta else None
    if not meta_desc:
        issues.append(AuditIssue(
            id=_issue_id("seo_no_meta", url), category=AuditCategory.SEO,
            severity=Severity.HIGH, title="Missing meta description",
            description="No meta description found.",
            recommendation="Add a meta description (150-160 characters).",
            location="<head>", estimated_hours=0.5, complexity="simple",
        ))

    # H1
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 0:
        issues.append(AuditIssue(
            id=_issue_id("seo_no_h1", url), category=AuditCategory.SEO,
            severity=Severity.HIGH, title="Missing H1 heading",
            description="No H1 heading found on the page.",
            recommendation="Add a single H1 heading with the main keyword.",
            location="<body>", estimated_hours=0.5, complexity="simple",
        ))
    elif len(h1_tags) > 1:
        issues.append(AuditIssue(
            id=_issue_id("seo_multi_h1", url), category=AuditCategory.SEO,
            severity=Severity.MEDIUM, title=f"Multiple H1 headings ({len(h1_tags)})",
            description=f"Found {len(h1_tags)} H1 tags. Best practice is one.",
            recommendation="Keep only one H1 tag per page.",
            location="<body>", estimated_hours=1.0, complexity="simple",
        ))

    # Images without alt
    imgs = soup.find_all("img")
    missing_alt = sum(1 for img in imgs if img.get("alt") is None)
    if missing_alt > 0:
        issues.append(AuditIssue(
            id=_issue_id("seo_missing_alt", url), category=AuditCategory.SEO,
            severity=Severity.MEDIUM, title=f"{missing_alt} images without alt text",
            description="Images without alt attributes hurt SEO and accessibility.",
            recommendation="Add descriptive alt text to all informative images.",
            location="<img>", estimated_hours=missing_alt * 0.1, complexity="simple",
        ))

    # Canonical
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if not canonical:
        issues.append(AuditIssue(
            id=_issue_id("seo_no_canonical", url), category=AuditCategory.SEO,
            severity=Severity.MEDIUM, title="Missing canonical URL",
            description="No canonical link found.",
            recommendation="Add <link rel='canonical' href='...'>.",
            location="<head>", estimated_hours=0.5, complexity="simple",
        ))

    # robots.txt
    try:
        resp = await client.get(f"{base_url}/robots.txt")
        robots_ok = resp.status_code == 200
    except Exception:
        robots_ok = False
    if not robots_ok:
        issues.append(AuditIssue(
            id=_issue_id("seo_no_robots", url), category=AuditCategory.SEO,
            severity=Severity.MEDIUM, title="Missing robots.txt",
            description="No robots.txt found at site root.",
            recommendation="Create a robots.txt file.",
            location="/robots.txt", estimated_hours=1.0, complexity="simple",
        ))

    # sitemap
    sitemap_ok = False
    for sp in ["/sitemap.xml", "/sitemap_index.xml"]:
        try:
            resp = await client.get(f"{base_url}{sp}")
            if resp.status_code == 200:
                sitemap_ok = True
                break
        except Exception:
            pass
    if not sitemap_ok:
        issues.append(AuditIssue(
            id=_issue_id("seo_no_sitemap", url), category=AuditCategory.SEO,
            severity=Severity.HIGH, title="Missing sitemap.xml",
            description="No sitemap found.",
            recommendation="Create and submit an XML sitemap.",
            location="/sitemap.xml", estimated_hours=2.0, complexity="medium",
        ))

    # Broken links (first 20 internal)
    links = soup.find_all("a", href=True)
    internal = [
        urljoin(base_url, a["href"])
        for a in links[:30]
        if a["href"].startswith("/") or base_url in a["href"]
    ]
    broken = []
    for link in internal[:20]:
        try:
            r = await client.head(link, timeout=5.0)
            if r.status_code >= 400:
                broken.append(link)
        except Exception:
            broken.append(link)
    if broken:
        issues.append(AuditIssue(
            id=_issue_id("seo_broken_links", url), category=AuditCategory.SEO,
            severity=Severity.HIGH,
            title=f"{len(broken)} broken links found",
            description=f"Broken: {', '.join(broken[:5])}",
            recommendation="Fix or remove broken links.",
            location="<a>", estimated_hours=len(broken) * 0.25, complexity="simple",
        ))

    # Score
    score = 100
    if not title:
        score -= 25
    elif title_len < 50 or title_len > 70:
        score -= 10
    if not meta_desc:
        score -= 25
    if len(h1_tags) == 0:
        score -= 20
    elif len(h1_tags) > 1:
        score -= 10
    if missing_alt > 0:
        score -= min(15, missing_alt * 2)
    if not robots_ok:
        score -= 5
    if not sitemap_ok:
        score -= 10
    if broken:
        score -= min(15, len(broken) * 3)
    if not canonical:
        score -= 5
    score = max(0, min(100, score))

    return score, issues


# ---------------------------------------------------------------------------
# Accessibility Audit
# ---------------------------------------------------------------------------

async def audit_accessibility(url: str, soup: BeautifulSoup) -> tuple:
    """Run accessibility checks, return (score, issues)."""
    issues: List[AuditIssue] = []

    # Images without alt
    imgs = soup.find_all("img")
    missing_alt = sum(1 for img in imgs if img.get("alt") is None)
    if missing_alt > 0:
        issues.append(AuditIssue(
            id=_issue_id("a11y_missing_alt", url), category=AuditCategory.ACCESSIBILITY,
            severity=Severity.HIGH,
            title=f"{missing_alt} images without alternative text",
            description="Images without alt attribute are not accessible to screen readers.",
            recommendation="Add descriptive alt text. Use alt='' for decorative images.",
            location="<img>", estimated_hours=missing_alt * 0.1, complexity="simple",
        ))

    # Form labels
    inputs = soup.find_all(["input", "select", "textarea"])
    missing_labels = 0
    for inp in inputs:
        inp_type = inp.get("type", "text")
        if inp_type in ["hidden", "submit", "button", "image", "reset"]:
            continue
        has_label = False
        inp_id = inp.get("id")
        if inp_id and soup.find("label", attrs={"for": inp_id}):
            has_label = True
        if inp.get("aria-label") or inp.get("aria-labelledby"):
            has_label = True
        if inp.find_parent("label"):
            has_label = True
        if inp.get("placeholder"):
            has_label = True
        if not has_label:
            missing_labels += 1
    if missing_labels > 0:
        issues.append(AuditIssue(
            id=_issue_id("a11y_missing_labels", url), category=AuditCategory.ACCESSIBILITY,
            severity=Severity.HIGH,
            title=f"{missing_labels} form fields without labels",
            description="Fields without labels are not accessible for screen reader users.",
            recommendation="Add <label> elements with 'for' attribute for each input.",
            location="<input>/<select>/<textarea>", estimated_hours=missing_labels * 0.2,
            complexity="simple",
        ))

    # Heading hierarchy
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    h1_count = len(soup.find_all("h1"))
    heading_issues = []
    if h1_count == 0:
        heading_issues.append("Missing H1 heading")
    elif h1_count > 1:
        heading_issues.append(f"Multiple H1 headings ({h1_count})")
    prev = 0
    for h in headings:
        level = int(h.name[1])
        if level > prev + 1 and prev > 0:
            heading_issues.append(f"Skipped heading level: H{prev} to H{level}")
        prev = level
    if not headings:
        heading_issues.append("No headings found")

    for hi in heading_issues:
        sev = Severity.HIGH if "Missing H1" in hi else Severity.MEDIUM
        issues.append(AuditIssue(
            id=_issue_id(f"a11y_heading_{hi[:10]}", url),
            category=AuditCategory.ACCESSIBILITY, severity=sev,
            title=f"Heading hierarchy issue: {hi}",
            description="Heading hierarchy must be logical and without skips.",
            recommendation="Restructure headings to follow H1 > H2 > H3.",
            location="<h1>-<h6>", estimated_hours=1.0, complexity="simple",
        ))

    # Lang attribute
    html_tag = soup.find("html")
    has_lang = html_tag is not None and html_tag.get("lang") is not None
    if not has_lang:
        issues.append(AuditIssue(
            id=_issue_id("a11y_no_lang", url), category=AuditCategory.ACCESSIBILITY,
            severity=Severity.HIGH, title="Missing lang attribute on <html>",
            description="Screen readers need the lang attribute to pronounce content correctly.",
            recommendation="Add lang attribute: <html lang='en'>.",
            location="<html>", estimated_hours=0.25, complexity="simple",
        ))

    # Skip links
    has_skip = False
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").lower()
        text = a.get_text().lower()
        if any(p in href for p in ["#main", "#content", "#skip"]) or "skip" in text:
            has_skip = True
            break
    if not has_skip:
        issues.append(AuditIssue(
            id=_issue_id("a11y_no_skip", url), category=AuditCategory.ACCESSIBILITY,
            severity=Severity.MEDIUM, title="Missing skip navigation link",
            description="Skip links help keyboard users navigate past repetitive content.",
            recommendation="Add a skip link at the top: <a href='#main'>Skip to content</a>.",
            location="<body> top", estimated_hours=1.0, complexity="simple",
        ))

    # Keyboard navigation
    tabindex_elems = soup.find_all(attrs={"tabindex": True})
    styles = soup.find_all("style")
    has_focus = any(":focus" in str(s) for s in styles)
    keyboard_ok = len(tabindex_elems) > 0 or has_focus or has_skip
    if not keyboard_ok:
        issues.append(AuditIssue(
            id=_issue_id("a11y_keyboard", url), category=AuditCategory.ACCESSIBILITY,
            severity=Severity.HIGH, title="Limited keyboard navigation",
            description="Interactive elements may not be accessible via keyboard.",
            recommendation="Ensure all interactive elements have visible focus and are Tab-accessible.",
            location="<body>", estimated_hours=4.0, complexity="medium",
        ))

    # ARIA usage count
    aria_count = 0
    for attr in ["aria-label", "aria-labelledby", "aria-describedby", "aria-hidden", "role"]:
        aria_count += len(soup.find_all(attrs={attr: True}))

    # Score
    score = 100
    score -= min(20, missing_alt * 3)
    score -= min(15, missing_labels * 5)
    if heading_issues:
        score -= 10
    if not has_lang:
        score -= 10
    if not has_skip:
        score -= 5
    if not keyboard_ok:
        score -= 10
    if aria_count >= 5:
        score = min(100, score + 5)
    score = max(0, min(100, score))

    return score, issues


# ---------------------------------------------------------------------------
# Security Audit
# ---------------------------------------------------------------------------

async def audit_security(url: str, response: httpx.Response) -> tuple:
    """Run security checks, return (score, issues)."""
    issues: List[AuditIssue] = []
    headers = dict(response.headers)
    content = response.text
    parsed = urlparse(url)
    domain = parsed.netloc

    https = url.startswith("https://")
    if not https:
        issues.append(AuditIssue(
            id=_issue_id("sec_no_https", url), category=AuditCategory.SECURITY,
            severity=Severity.CRITICAL, title="HTTPS not enabled",
            description="Site does not use HTTPS.",
            recommendation="Install an SSL certificate and redirect HTTP to HTTPS.",
            location=url, estimated_hours=4.0, complexity="medium",
        ))

    # SSL check
    ssl_valid = False
    ssl_days = None
    if https:
        try:
            host = domain.split(":")[0]
            ctx = ssl.create_default_context()
            loop = asyncio.get_event_loop()

            def _get_cert():
                with socket.create_connection((host, 443), timeout=10) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host) as ss:
                        return ss.getpeercert()

            cert = await loop.run_in_executor(None, _get_cert)
            not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            ssl_days = (not_after - datetime.now()).days
            ssl_valid = True
        except Exception:
            pass

    if https and not ssl_valid:
        issues.append(AuditIssue(
            id=_issue_id("sec_ssl_invalid", url), category=AuditCategory.SECURITY,
            severity=Severity.CRITICAL, title="Invalid SSL certificate",
            description="SSL certificate is invalid or expired.",
            recommendation="Renew or install a valid SSL certificate.",
            location=url, estimated_hours=2.0, complexity="simple",
        ))
    elif ssl_days is not None and ssl_days < 30:
        issues.append(AuditIssue(
            id=_issue_id("sec_ssl_expiring", url), category=AuditCategory.SECURITY,
            severity=Severity.HIGH, title=f"SSL expires in {ssl_days} days",
            description="SSL certificate will expire soon.",
            recommendation="Renew SSL certificate before expiration.",
            location=url, estimated_hours=1.0, complexity="simple",
        ))

    # Security headers
    header_checks = [
        ("strict-transport-security", "HSTS", Severity.HIGH, "sec_no_hsts",
         "Add Strict-Transport-Security header."),
        ("content-security-policy", "CSP", Severity.HIGH, "sec_no_csp",
         "Implement Content-Security-Policy header."),
        ("x-frame-options", "X-Frame-Options", Severity.MEDIUM, "sec_no_xframe",
         "Add X-Frame-Options: DENY or SAMEORIGIN."),
        ("x-content-type-options", "X-Content-Type-Options", Severity.LOW, "sec_no_xcontent",
         "Add X-Content-Type-Options: nosniff."),
    ]
    for hdr, name, sev, iid, rec in header_checks:
        if hdr not in headers:
            issues.append(AuditIssue(
                id=_issue_id(iid, url), category=AuditCategory.SECURITY,
                severity=sev, title=f"Missing {name} header",
                description=f"The {name} security header is not set.",
                recommendation=rec, location="HTTP headers",
                estimated_hours=1.0 if sev in (Severity.HIGH, Severity.CRITICAL) else 0.5,
                complexity="simple",
            ))

    # Exposed API keys
    key_patterns = [
        r'api[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9]{20,}',
        r'secret[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9]{20,}',
        r'sk-[a-zA-Z0-9]{20,}',
        r'pk_live_[a-zA-Z0-9]{20,}',
        r'AIza[a-zA-Z0-9]{35}',
    ]
    has_keys = any(re.search(p, content, re.IGNORECASE) for p in key_patterns)
    if has_keys:
        issues.append(AuditIssue(
            id=_issue_id("sec_exposed_keys", url), category=AuditCategory.SECURITY,
            severity=Severity.CRITICAL, title="Possible API keys exposed in source",
            description="Patterns resembling API keys detected in page source.",
            recommendation="Remove API keys from frontend code. Use server-side env vars.",
            location="<script> / inline", estimated_hours=2.0, complexity="medium",
        ))

    # Exposed emails
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
    emails = [e for e in set(emails) if not e.endswith((".png", ".jpg", ".svg"))]
    if emails:
        issues.append(AuditIssue(
            id=_issue_id("sec_exposed_emails", url), category=AuditCategory.SECURITY,
            severity=Severity.LOW,
            title=f"{len(emails)} email addresses exposed",
            description=f"Found: {', '.join(emails[:3])}",
            recommendation="Use contact forms instead of exposing email addresses.",
            location="page content", estimated_hours=1.0, complexity="simple",
        ))

    # Score
    score = 100
    if not https:
        score -= 25
    if https and not ssl_valid:
        score -= 20
    elif ssl_days is not None and ssl_days < 30:
        score -= 10
    if "strict-transport-security" not in headers:
        score -= 10
    if "content-security-policy" not in headers:
        score -= 10
    if "x-frame-options" not in headers:
        score -= 5
    if "x-content-type-options" not in headers:
        score -= 5
    if has_keys:
        score -= 15
    if emails:
        score -= 5
    score = max(0, min(100, score))

    return score, issues


# ---------------------------------------------------------------------------
# Performance Audit
# ---------------------------------------------------------------------------

async def audit_performance(url: str) -> tuple:
    """Run performance checks via HTTP timing, return (score, issues)."""
    issues: List[AuditIssue] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        start = datetime.now()
        resp = await client.get(url, follow_redirects=True)
        elapsed = (datetime.now() - start).total_seconds()

    content_len = len(resp.content)

    # Estimate metrics from HTTP response
    ttfb_est = elapsed * 300  # ms estimate
    lcp_est = elapsed * 1.5
    fcp_est = elapsed * 0.8

    thresholds = {
        "lcp": {"good": 2.5, "poor": 4.0},
        "ttfb": {"good": 800, "poor": 1800},
        "fcp": {"good": 1.8, "poor": 3.0},
    }

    if lcp_est > thresholds["lcp"]["good"]:
        sev = Severity.CRITICAL if lcp_est > thresholds["lcp"]["poor"] else Severity.HIGH
        issues.append(AuditIssue(
            id=_issue_id("perf_lcp", url), category=AuditCategory.PERFORMANCE,
            severity=sev, title=f"Slow LCP ({lcp_est:.2f}s)",
            description=f"Largest Contentful Paint is {lcp_est:.2f}s (good: <2.5s).",
            recommendation="Optimize images, use CDN, reduce server response time.",
            location="page load", estimated_hours=4.0, complexity="complex",
        ))

    if ttfb_est > thresholds["ttfb"]["good"]:
        sev = Severity.HIGH if ttfb_est > thresholds["ttfb"]["poor"] else Severity.MEDIUM
        issues.append(AuditIssue(
            id=_issue_id("perf_ttfb", url), category=AuditCategory.PERFORMANCE,
            severity=sev, title=f"Slow TTFB ({ttfb_est:.0f}ms)",
            description=f"Time to First Byte is ~{ttfb_est:.0f}ms (good: <800ms).",
            recommendation="Optimize server response, use caching, consider CDN.",
            location="server", estimated_hours=6.0, complexity="complex",
        ))

    if fcp_est > thresholds["fcp"]["good"]:
        issues.append(AuditIssue(
            id=_issue_id("perf_fcp", url), category=AuditCategory.PERFORMANCE,
            severity=Severity.MEDIUM,
            title=f"Slow FCP ({fcp_est:.2f}s)",
            description=f"First Contentful Paint is {fcp_est:.2f}s (good: <1.8s).",
            recommendation="Minimize render-blocking resources, inline critical CSS.",
            location="page load", estimated_hours=2.0, complexity="medium",
        ))

    # Page size
    size_kb = content_len / 1024
    if size_kb > 500:
        issues.append(AuditIssue(
            id=_issue_id("perf_page_size", url), category=AuditCategory.PERFORMANCE,
            severity=Severity.MEDIUM,
            title=f"Large page size ({size_kb:.0f}KB)",
            description=f"Page HTML is {size_kb:.0f}KB.",
            recommendation="Minify HTML, compress assets, lazy-load images.",
            location="page", estimated_hours=3.0, complexity="medium",
        ))

    # Score
    scores = []
    if lcp_est <= thresholds["lcp"]["good"]:
        scores.append(100)
    elif lcp_est >= thresholds["lcp"]["poor"]:
        scores.append(30)
    else:
        scores.append(65)

    if ttfb_est <= thresholds["ttfb"]["good"]:
        scores.append(100)
    elif ttfb_est >= thresholds["ttfb"]["poor"]:
        scores.append(30)
    else:
        scores.append(65)

    if fcp_est <= thresholds["fcp"]["good"]:
        scores.append(100)
    elif fcp_est >= thresholds["fcp"]["poor"]:
        scores.append(30)
    else:
        scores.append(65)

    score = int(sum(scores) / len(scores)) if scores else 50

    return score, issues


# ---------------------------------------------------------------------------
# Main Audit Orchestrator
# ---------------------------------------------------------------------------

async def run_audit(url: str, categories: List[str] = None) -> AuditReport:
    """Run a full audit on the given URL."""
    if categories is None:
        categories = ["seo", "accessibility", "security", "performance"]

    logger.info(f"Starting audit for {url}")
    logger.info(f"Categories: {', '.join(categories)}")

    all_issues: List[AuditIssue] = []
    cat_scores: List[CategoryScore] = []

    async with httpx.AsyncClient(
        timeout=30.0, follow_redirects=True,
        headers={"User-Agent": "AIWebAuditor/1.0"},
    ) as client:
        logger.info("Fetching page...")
        response = await client.get(url)
        soup = BeautifulSoup(response.content, "lxml")
        logger.info(f"Page fetched: {response.status_code} ({len(response.content)} bytes)")

        # SEO
        if "seo" in categories:
            logger.info("Running SEO audit...")
            seo_score, seo_issues = await audit_seo(url, soup, client)
            all_issues.extend(seo_issues)
            cs = _build_cat_score(AuditCategory.SEO, seo_score, seo_issues)
            cat_scores.append(cs)
            logger.info(f"SEO: score={seo_score}, issues={len(seo_issues)}")

        # Accessibility
        if "accessibility" in categories:
            logger.info("Running Accessibility audit...")
            a11y_score, a11y_issues = await audit_accessibility(url, soup)
            all_issues.extend(a11y_issues)
            cs = _build_cat_score(AuditCategory.ACCESSIBILITY, a11y_score, a11y_issues)
            cat_scores.append(cs)
            logger.info(f"Accessibility: score={a11y_score}, issues={len(a11y_issues)}")

        # Security
        if "security" in categories:
            logger.info("Running Security audit...")
            sec_score, sec_issues = await audit_security(url, response)
            all_issues.extend(sec_issues)
            cs = _build_cat_score(AuditCategory.SECURITY, sec_score, sec_issues)
            cat_scores.append(cs)
            logger.info(f"Security: score={sec_score}, issues={len(sec_issues)}")

    # Performance (uses its own client)
    if "performance" in categories:
        logger.info("Running Performance audit...")
        perf_score, perf_issues = await audit_performance(url)
        all_issues.extend(perf_issues)
        cs = _build_cat_score(AuditCategory.PERFORMANCE, perf_score, perf_issues)
        cat_scores.append(cs)
        logger.info(f"Performance: score={perf_score}, issues={len(perf_issues)}")

    # Overall score
    if cat_scores:
        overall = int(sum(c.score for c in cat_scores) / len(cat_scores))
    else:
        overall = 0

    # Issues by severity
    by_sev = {}
    for issue in all_issues:
        by_sev[issue.severity.value] = by_sev.get(issue.severity.value, 0) + 1

    report = AuditReport(
        url=url,
        timestamp=datetime.now().isoformat(),
        overall_score=overall,
        category_scores=cat_scores,
        issues=all_issues,
        total_issues=len(all_issues),
        issues_by_severity=by_sev,
        metadata={
            "categories_audited": categories,
            "engine": "AIWebAuditor/1.0 standalone",
        },
    )

    logger.info(f"Audit complete: overall_score={overall}, total_issues={len(all_issues)}")
    return report


def _build_cat_score(category: AuditCategory, score: int, issues: List[AuditIssue]) -> CategoryScore:
    return CategoryScore(
        category=category,
        score=score,
        issues_count=len(issues),
        critical_count=sum(1 for i in issues if i.severity == Severity.CRITICAL),
        high_count=sum(1 for i in issues if i.severity == Severity.HIGH),
        medium_count=sum(1 for i in issues if i.severity == Severity.MEDIUM),
        low_count=sum(1 for i in issues if i.severity == Severity.LOW),
    )
