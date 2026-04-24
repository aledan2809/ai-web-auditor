"""
Retest Engine - Re-audits after fixes and generates comparison report
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..schemas.models import (
    AuditReport,
    IssueStatus,
    RetestComparison,
    RetestReport,
)
from .auditor import run_audit

logger = logging.getLogger("aiwebauditor")


async def run_retest(
    url: str,
    original_report: AuditReport,
    categories: List[str] = None,
) -> RetestReport:
    """Re-audit a URL and compare with original audit results."""
    logger.info(f"Starting retest for {url}")
    logger.info(f"Original audit had {original_report.total_issues} issues")

    # Run fresh audit
    if categories is None:
        categories = original_report.metadata.get(
            "categories_audited",
            ["seo", "accessibility", "security", "performance"],
        )

    retest_audit = await run_audit(url, categories)

    # Build comparison
    original_ids = {i.id: i for i in original_report.issues}
    retest_ids = {i.id: i for i in retest_audit.issues}

    comparisons: List[RetestComparison] = []
    resolved = 0
    remaining = 0

    # Check each original issue
    for oid, orig_issue in original_ids.items():
        if oid not in retest_ids:
            comparisons.append(RetestComparison(
                issue_id=oid,
                title=orig_issue.title,
                severity=orig_issue.severity.value,
                status=IssueStatus.FIXED,
                original_description=orig_issue.description,
                retest_description="Issue resolved.",
            ))
            resolved += 1
        else:
            retest_issue = retest_ids[oid]
            comparisons.append(RetestComparison(
                issue_id=oid,
                title=orig_issue.title,
                severity=orig_issue.severity.value,
                status=IssueStatus.NOT_FIXED,
                original_description=orig_issue.description,
                retest_description=retest_issue.description,
            ))
            remaining += 1

    # New issues (in retest but not in original)
    new_issues = 0
    for rid, retest_issue in retest_ids.items():
        if rid not in original_ids:
            comparisons.append(RetestComparison(
                issue_id=rid,
                title=retest_issue.title,
                severity=retest_issue.severity.value,
                status=IssueStatus.OPEN,
                original_description="(new issue)",
                retest_description=retest_issue.description,
            ))
            new_issues += 1

    total_orig = len(original_ids)
    pct = (resolved / total_orig * 100) if total_orig > 0 else 0.0

    report = RetestReport(
        original_audit=original_report.url,
        retest_timestamp=datetime.now().isoformat(),
        url=url,
        original_score=original_report.overall_score,
        retest_score=retest_audit.overall_score,
        score_change=retest_audit.overall_score - original_report.overall_score,
        total_original_issues=total_orig,
        resolved_issues=resolved,
        remaining_issues=remaining,
        new_issues=new_issues,
        resolved_percentage=round(pct, 1),
        comparisons=comparisons,
        issues=retest_audit.issues,
    )

    logger.info(
        f"Retest complete: {resolved}/{total_orig} resolved ({pct:.1f}%), "
        f"score {original_report.overall_score} -> {retest_audit.overall_score}"
    )

    return report
