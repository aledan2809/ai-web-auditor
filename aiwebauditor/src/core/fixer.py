"""
Fix Engine - Generates patches/diffs for audit issues
"""

import difflib
import json
import logging
import os
import re
import shutil
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from ..schemas.models import AuditIssue, AuditReport, FixPatch, FixReport, Severity

logger = logging.getLogger("aiwebauditor")


# Map of issue ID prefixes to fix functions
FIX_REGISTRY: Dict[str, callable] = {}


def _register_fix(prefix: str):
    def decorator(fn):
        FIX_REGISTRY[prefix] = fn
        return fn
    return decorator


@_register_fix("seo_no_title")
def fix_no_title(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    head = soup.find("head")
    if not head:
        return None
    title_tag = soup.new_tag("title")
    title_tag.string = "Page Title - Update with relevant keywords"
    head.append(title_tag)
    return str(soup), "Added missing <title> tag"


@_register_fix("seo_short_title")
def fix_short_title(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.find("title")
    if not title:
        return None
    current = title.get_text().strip()
    title.string = current + " - Expand with relevant keywords and description"
    return str(soup), "Expanded short <title> tag"


@_register_fix("seo_no_meta")
def fix_no_meta(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    head = soup.find("head")
    if not head:
        return None
    meta = soup.new_tag("meta", attrs={"name": "description", "content": "Update this with a descriptive meta description (150-160 characters)"})
    head.append(meta)
    return str(soup), "Added missing meta description"


@_register_fix("seo_no_canonical")
def fix_no_canonical(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    head = soup.find("head")
    if not head:
        return None
    link = soup.new_tag("link", attrs={"rel": "canonical", "href": "UPDATE_WITH_CANONICAL_URL"})
    head.append(link)
    return str(soup), "Added canonical link (update href)"


@_register_fix("seo_no_h1")
def fix_no_h1(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    body = soup.find("body")
    if not body:
        return None
    h1 = soup.new_tag("h1")
    h1.string = "Main Heading - Update with page topic"
    body.insert(0, h1)
    return str(soup), "Added missing H1 heading"


@_register_fix("a11y_no_lang")
def fix_no_lang(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    html_tag = soup.find("html")
    if html_tag:
        html_tag["lang"] = "en"
    else:
        return None
    return str(soup), "Added lang='en' to <html>"


@_register_fix("a11y_missing_alt")
def fix_missing_alt(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    imgs = soup.find_all("img")
    fixed = 0
    for img in imgs:
        if img.get("alt") is None:
            src = img.get("src", "image")
            name = os.path.splitext(os.path.basename(src))[0] if src else "image"
            img["alt"] = f"Image: {name} - update with descriptive text"
            fixed += 1
    if fixed == 0:
        return None
    return str(soup), f"Added placeholder alt text to {fixed} images"


@_register_fix("a11y_no_skip")
def fix_no_skip(html: str, issue: AuditIssue) -> Optional[tuple]:
    soup = BeautifulSoup(html, "lxml")
    body = soup.find("body")
    if not body:
        return None
    skip = soup.new_tag("a", href="#main", attrs={"class": "skip-link"})
    skip.string = "Skip to main content"
    body.insert(0, skip)
    # Add id=main to first main or first div
    main = soup.find("main") or soup.find("div")
    if main and not main.get("id"):
        main["id"] = "main"
    return str(soup), "Added skip navigation link"


@_register_fix("sec_no_xcontent")
def fix_no_xcontent(html: str, issue: AuditIssue) -> Optional[tuple]:
    # This is a server config fix, return instruction
    return None


def generate_diff(original: str, fixed: str, filename: str = "page.html") -> str:
    """Generate unified diff between original and fixed content."""
    orig_lines = original.splitlines(keepends=True)
    fixed_lines = fixed.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines, fixed_lines,
        fromfile=f"a/{filename}", tofile=f"b/{filename}",
    )
    return "".join(diff)


def generate_fixes(audit_report: AuditReport, html_content: str = None) -> FixReport:
    """Generate fix patches for all fixable issues in the audit report."""
    logger.info(f"Generating fixes for {audit_report.total_issues} issues")

    patches: List[FixPatch] = []
    unfixable: Dict[str, str] = {}

    for issue in audit_report.issues:
        # Find matching fix function by prefix
        fix_fn = None
        for prefix, fn in FIX_REGISTRY.items():
            if issue.id.startswith(prefix):
                fix_fn = fn
                break

        if fix_fn is None:
            unfixable[issue.id] = f"No auto-fix available for {issue.title}"
            continue

        if html_content is None:
            unfixable[issue.id] = "No HTML content provided for fixing"
            continue

        result = fix_fn(html_content, issue)
        if result is None:
            unfixable[issue.id] = f"Fix could not be applied: {issue.title}"
            continue

        fixed_html, description = result
        diff = generate_diff(html_content, fixed_html)

        if diff:
            patches.append(FixPatch(
                issue_id=issue.id,
                original=html_content[:200] + "...",
                fixed=fixed_html[:200] + "...",
                diff=diff,
                description=description,
                auto_applicable=True,
            ))
            # Update html_content for subsequent fixes
            html_content = fixed_html

    fix_report = FixReport(
        source_audit=audit_report.url,
        timestamp=__import__("datetime").datetime.now().isoformat(),
        total_issues=audit_report.total_issues,
        fixable_issues=len(patches),
        patches_generated=len(patches),
        patches=patches,
        unfixable_reasons=unfixable,
    )

    logger.info(f"Fixes generated: {len(patches)} patches, {len(unfixable)} unfixable")
    return fix_report


def apply_fixes(html_content: str, fix_report: FixReport, backup: bool = True) -> str:
    """Apply all patches sequentially to the HTML content."""
    current = html_content

    for patch in fix_report.patches:
        if not patch.auto_applicable:
            continue

        # Re-run the fix on current content
        for prefix, fn in FIX_REGISTRY.items():
            if patch.issue_id.startswith(prefix):
                result = fn(current, None)
                if result:
                    current, _ = result
                break

    return current
