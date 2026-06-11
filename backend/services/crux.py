"""
CrUX field data — real-user Core Web Vitals from the Chrome UX Report API
(secondary roadmap item, test-tooling 2026-06-11).

The performance auditor measures ONLY synthetically (one Playwright load from
the audit box). CrUX adds p75 field data from real Chrome users — the same
numbers Google Search uses — which is what gives a paid audit credibility.

Flag-gated: no-op unless CRUX_API_KEY is set in the environment (Google Cloud
API key with the Chrome UX Report API enabled). Missing key / URL not in the
CrUX dataset / network error → returns None and the audit proceeds purely
synthetic, exactly as before.

Pure parse/assess/issue builders are IO-free and unit-tested; only
fetch_crux_metrics talks to the network (httpx, injectable for tests).
"""

import os
from typing import Optional

import httpx

from models.schemas import AuditIssue, AuditType, Severity

CRUX_ENDPOINT = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"

# p75 thresholds per web.dev: (good, poor)
CRUX_THRESHOLDS = {
    "largest_contentful_paint": (2500, 4000),      # ms
    "interaction_to_next_paint": (200, 500),       # ms
    "cumulative_layout_shift": (0.1, 0.25),        # unitless
}

METRIC_LABELS = {
    "largest_contentful_paint": "LCP",
    "interaction_to_next_paint": "INP",
    "cumulative_layout_shift": "CLS",
}


def parse_crux_record(data: dict) -> Optional[dict]:
    """
    Extract p75 values for the three Core Web Vitals from a CrUX API response.
    Returns {metric_key: p75_float} for the metrics present, or None when the
    response carries no usable record (URL not in dataset, malformed, etc).
    """
    metrics = (data or {}).get("record", {}).get("metrics", {})
    out = {}
    for key in CRUX_THRESHOLDS:
        p75 = metrics.get(key, {}).get("percentiles", {}).get("p75")
        if p75 is None:
            continue
        try:
            out[key] = float(p75)
        except (TypeError, ValueError):
            continue
    return out or None


def rate_metric(key: str, p75: float) -> str:
    """'good' | 'needs-improvement' | 'poor' per web.dev thresholds."""
    good, poor = CRUX_THRESHOLDS[key]
    if p75 <= good:
        return "good"
    if p75 <= poor:
        return "needs-improvement"
    return "poor"


def _fmt(key: str, p75: float) -> str:
    if key == "cumulative_layout_shift":
        return f"{p75:.2f}"
    return f"{p75 / 1000:.2f}s" if key == "largest_contentful_paint" else f"{p75:.0f}ms"


def crux_issues(parsed: dict, url: str, lang: str = "ro") -> list:
    """
    AuditIssue list for non-good field metrics. Severity: poor → HIGH,
    needs-improvement → MEDIUM. Good metrics produce nothing — the synthetic
    auditor already covers the rest of the story.
    """
    issues = []
    for key, p75 in (parsed or {}).items():
        rating = rate_metric(key, p75)
        if rating == "good":
            continue
        label = METRIC_LABELS[key]
        value = _fmt(key, p75)
        severity = Severity.HIGH if rating == "poor" else Severity.MEDIUM
        if lang == "en":
            title = f"Real-user {label} is {rating} (p75 {value})"
            description = (
                f"Chrome UX Report field data for {url}: p75 {label} = {value} "
                f"({rating}). This is what real Chrome users experience and what "
                f"Google Search uses for ranking signals — independent of our lab test."
            )
            recommendation = f"Bring p75 {label} into the 'good' range; field data updates with a ~28-day window."
        else:
            title = f"{label} la utilizatori reali: {rating} (p75 {value})"
            description = (
                f"Date de teren Chrome UX Report pentru {url}: p75 {label} = {value} "
                f"({rating}). Asta experimentează utilizatorii reali de Chrome și pe asta "
                f"se bazează Google Search — independent de testul nostru de laborator."
            )
            recommendation = f"Adu p75 {label} în zona 'good'; datele de teren se actualizează pe fereastră de ~28 zile."
        issues.append(AuditIssue(
            id=f"crux_{label.lower()}_{abs(hash(url))}",
            category=AuditType.PERFORMANCE,
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            estimated_hours=4.0 if rating == "poor" else 2.0,
            complexity="complex" if rating == "poor" else "medium",
        ))
    return issues


async def fetch_crux_metrics(
    url: str,
    api_key: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
    form_factor: str = "PHONE",
) -> Optional[dict]:
    """
    Query the CrUX API for p75 field data. Returns parse_crux_record() output
    or None on any failure (missing key, URL not in dataset → 404, network).
    Never raises — field data is a credibility bonus, not a dependency.
    """
    key = api_key or os.environ.get("CRUX_API_KEY")
    if not key:
        return None
    own_client = client is None
    client = client or httpx.AsyncClient(timeout=10)
    try:
        resp = await client.post(
            f"{CRUX_ENDPOINT}?key={key}",
            json={"url": url, "formFactor": form_factor},
        )
        if resp.status_code != 200:
            return None
        return parse_crux_record(resp.json())
    except Exception:
        return None
    finally:
        if own_client:
            await client.aclose()
