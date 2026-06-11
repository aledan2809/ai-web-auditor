"""
Concurrent auditor execution (roadmap R5).

The 11 auditors are independent network/analysis tasks but main.py awaits each
one inline-sequentially, so total audit time = SUM of auditor times. This helper
runs the `.audit()` calls CONCURRENTLY (asyncio.gather) so total ≈ MAX, while
preserving the EXACT error policy main.py had:

  - "core" auditors (performance/seo/security/gdpr/accessibility) were awaited
    in the outer try with no per-auditor guard → one failure fails the whole
    audit. Gathered with plain gather() (first exception propagates) → identical.
  - "extra" auditors (mobile_ux/trust/competitor) had their own try/except that
    logged + continued → soft-fail. Gathered with return_exceptions=True and
    mapped to None on error → identical.

main.py keeps all metric-save + issue-collection logic; it only reads the
pre-computed `.audit()` result from the returned dict instead of awaiting inline.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Optional

logger = logging.getLogger("audit_runner")

# spec: (name, policy "core"|"extra", select_key, factory(url, mobile, lang) -> awaitable)
AuditorFactory = Callable[[str, bool, str], Awaitable]


def _default_specs() -> list[tuple]:
    from auditors.performance import PerformanceAuditor
    from auditors.seo import SEOAuditor
    from auditors.security import SecurityAuditor
    from auditors.gdpr import GDPRAuditor
    from auditors.accessibility import AccessibilityAuditor
    from auditors.mobile_ux import MobileUXAuditor
    from auditors.trust import TrustAuditor
    from auditors.competitor import CompetitorAuditor

    return [
        ("performance", "core", "performance", lambda url, mobile, lang: PerformanceAuditor().audit(url, mobile, lang)),
        ("seo", "core", "seo", lambda url, mobile, lang: SEOAuditor().audit(url, lang)),
        ("security", "core", "security", lambda url, mobile, lang: SecurityAuditor().audit(url, lang)),
        ("gdpr", "core", "gdpr", lambda url, mobile, lang: GDPRAuditor().audit(url, lang)),
        ("accessibility", "core", "accessibility", lambda url, mobile, lang: AccessibilityAuditor().audit(url, lang)),
        ("mobile_ux", "extra", None, lambda url, mobile, lang: MobileUXAuditor().audit(url, lang)),
        ("trust", "extra", None, lambda url, mobile, lang: TrustAuditor().audit(url, lang)),
        ("competitor", "extra", None, lambda url, mobile, lang: CompetitorAuditor().audit(url, competitor_url=None, lang=lang)),
    ]


def select_auditors(audit_types: list[str], specs: list[tuple]) -> list[tuple]:
    """Mirror main.py's in-scope conditions: core by name-or-full; extras only on full."""
    full = "full" in audit_types
    out = []
    for spec in specs:
        name, policy, key, _ = spec
        if policy == "core":
            if full or (key in audit_types):
                out.append(spec)
        else:  # extra
            if full:
                out.append(spec)
    return out


async def gather_auditor_results(
    url: str,
    audit_types: list[str],
    mobile_test: bool = True,
    lang: str = "ro",
    specs: Optional[list[tuple]] = None,
) -> dict:
    """
    Run all in-scope auditors concurrently. Returns {name: result_or_None}.
    Core exceptions propagate (hard-fail, like the old outer try); extra
    exceptions are caught + logged + mapped to None (soft-fail, like the old
    per-extra try/except).
    """
    specs = specs if specs is not None else _default_specs()
    selected = select_auditors(audit_types, specs)
    core = [s for s in selected if s[1] == "core"]
    extra = [s for s in selected if s[1] == "extra"]

    results: dict = {}

    # Kick BOTH groups off together, then await with their respective policies.
    core_task = asyncio.gather(*[s[3](url, mobile_test, lang) for s in core]) if core else None
    extra_task = asyncio.gather(*[s[3](url, mobile_test, lang) for s in extra], return_exceptions=True) if extra else None

    if extra_task is not None:
        extra_res = await extra_task
        for spec, r in zip(extra, extra_res):
            if isinstance(r, Exception):
                logger.warning(f"{spec[0]} audit error: {r}")
                results[spec[0]] = None
            else:
                results[spec[0]] = r

    if core_task is not None:
        core_res = await core_task  # first exception propagates (hard-fail preserved)
        for spec, r in zip(core, core_res):
            results[spec[0]] = r

    return results
