"""
AI Web Auditor — Recurring Monitoring (roadmap R3)

Turns the one-shot auditor into a subscription: periodically re-audit a site,
compare against the previous run, and email the owner ONLY when the score moved
(with a per-category breakdown of what changed).

Design mirrors the existing email_scheduler background loop. The pure decision
core (cadence + delta math + email composition) is IO-free and unit-tested; the
loop wires it to DB + the audit pipeline + email_service via seams so it stays
testable and the transports can be swapped.

Monitors source (no schema migration required): data/monitors.json —
  [ { "url": "https://x.com", "email": "owner@x.com", "frequency": "weekly",
      "last_audit_at": "2026-06-01T10:00:00Z", "last_overall": 82,
      "last_scores": { "performance": 70, "seo": 90, ... } } ]
The loop updates last_* in place after each re-audit.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional

logger = logging.getLogger("monitoring")

# Cadence in days per frequency keyword.
FREQUENCY_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}

# Score categories tracked for the delta breakdown.
SCORE_KEYS = [
    "performance", "seo", "security", "gdpr",
    "accessibility", "mobile_ux", "trust", "competitor",
]

# Only email when the absolute overall delta meets this floor (avoid noise from
# 1-point jitter between runs).
MIN_OVERALL_DELTA = 3


# ── Pure decision core (IO-free, unit-tested) ────────────────────────────────

def parse_iso(s: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 string into an aware UTC datetime (None-safe)."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def is_due(last_audit_at: Optional[str], frequency: str, now: datetime) -> bool:
    """
    True when a monitor is due for re-audit: never audited, unknown frequency
    (treated as weekly), or the cadence interval has elapsed.
    """
    last = parse_iso(last_audit_at)
    if last is None:
        return True
    days = FREQUENCY_DAYS.get((frequency or "weekly").lower(), 7)
    return now >= last + timedelta(days=days)


@dataclass
class ScoreDelta:
    key: str
    previous: int
    current: int

    @property
    def delta(self) -> int:
        return self.current - self.previous

    @property
    def direction(self) -> str:
        if self.delta > 0:
            return "up"
        if self.delta < 0:
            return "down"
        return "flat"


def score_deltas(previous: dict, current: dict) -> list[ScoreDelta]:
    """Per-category deltas — only for categories present in BOTH runs."""
    out = []
    for k in SCORE_KEYS:
        if previous.get(k) is None or current.get(k) is None:
            continue
        out.append(ScoreDelta(k, int(previous[k]), int(current[k])))
    return out


def overall_delta(previous_overall: int, current_overall: int) -> int:
    return int(current_overall) - int(previous_overall)


def should_notify(previous_overall: Optional[int], current_overall: int) -> bool:
    """
    Notify only on a meaningful overall move. First-ever run (no previous) does
    NOT notify here — that's the preview_ready email's job, not monitoring.
    """
    if previous_overall is None:
        return False
    return abs(overall_delta(previous_overall, current_overall)) >= MIN_OVERALL_DELTA


def summarize_deltas(deltas: list[ScoreDelta]) -> str:
    """One-line human summary of the biggest movers (worsened first)."""
    moved = [d for d in deltas if d.delta != 0]
    if not moved:
        return "No category changed."
    moved.sort(key=lambda d: d.delta)  # most-negative first
    parts = [f"{d.key} {d.previous}→{d.current} ({'+' if d.delta > 0 else ''}{d.delta})" for d in moved]
    return "; ".join(parts)


def build_delta_email(url: str, previous_overall: int, current_overall: int,
                      deltas: list[ScoreDelta]) -> tuple[str, str]:
    """Return (subject, plain-text body) for the change notification."""
    d = overall_delta(previous_overall, current_overall)
    arrow = "▲" if d > 0 else "▼"
    sign = "+" if d > 0 else ""
    subject = f"{arrow} Your site score changed: {previous_overall}→{current_overall} ({sign}{d}) — {url}"
    lines = [
        f"Your monitored site {url} was re-audited.",
        "",
        f"Overall score: {previous_overall} → {current_overall} ({sign}{d})",
        "",
        "What changed:",
    ]
    moved = [x for x in deltas if x.delta != 0]
    moved.sort(key=lambda x: x.delta)
    if moved:
        for x in moved:
            s = "+" if x.delta > 0 else ""
            lines.append(f"  • {x.key}: {x.previous} → {x.current} ({s}{x.delta})")
    else:
        lines.append("  • Overall moved but no single category crossed the threshold.")
    return subject, "\n".join(lines)


# ── IO loop (seams for DB / audit pipeline / email) ──────────────────────────

DEFAULT_MONITORS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "monitors.json"
)


def load_monitors(path: str = DEFAULT_MONITORS_PATH) -> list[dict]:
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_monitors(monitors: list[dict], path: str = DEFAULT_MONITORS_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(monitors, f, indent=2)


async def default_run_audit(url: str) -> Optional[dict]:
    """
    Real run-audit seam: runs the auditors CONCURRENTLY (reuses R5a's
    gather_auditor_results) + computes the official overall score, WITHOUT
    creating a full DB audit record. Returns {overall, scores}. Best-effort —
    returns None on failure so the monitor loop just skips this tick.
    """
    try:
        from services.audit_runner import gather_auditor_results
        from services.scoring import from_legacy_scores, compute_overall_score

        ar = await gather_auditor_results(url, ["full"], mobile_test=False, lang="ro")

        def sc(name):
            r = ar.get(name)
            return getattr(r, "score", None) if r is not None else None

        scores = {k: sc(k) for k in SCORE_KEYS}
        comp = from_legacy_scores(
            performance_score=scores.get("performance"),
            seo_score=scores.get("seo"),
            security_score=scores.get("security"),
            gdpr_score=scores.get("gdpr"),
            accessibility_score=scores.get("accessibility"),
            mobile_ux_score=scores.get("mobile_ux"),
            trust_score=scores.get("trust"),
            competitor_score=scores.get("competitor"),
        )
        overall = compute_overall_score(comp).overall_score
        return {"overall": int(round(overall)), "scores": {k: v for k, v in scores.items() if v is not None}}
    except Exception as e:
        logger.warning(f"monitoring run_audit failed for {url}: {e}")
        return None


async def run_monitoring_loop(poll_interval_seconds: int = 3600):
    """
    Background loop: every `poll_interval_seconds`, run one monitoring tick with
    the real audit + email seams. No-op while monitors.json is empty/absent, so
    enabling this is safe — it does nothing until a monitor is registered.
    """
    from services.email_service import _send

    logger.info("[MONITORING] Recurring re-audit loop started")
    while True:
        try:
            res = await run_monitoring_once(run_audit=default_run_audit, send_email=_send)
            if res["audited"]:
                logger.info(f"[MONITORING] tick: {res}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"[MONITORING] tick error: {e}")
        await asyncio.sleep(poll_interval_seconds)


async def run_monitoring_once(
    *,
    now: Optional[datetime] = None,
    monitors_path: str = DEFAULT_MONITORS_PATH,
    run_audit: Optional[Callable] = None,
    send_email: Optional[Callable[[str, str, str], bool]] = None,
) -> dict:
    """
    One monitoring tick: for every due monitor, re-audit, diff vs last run, and
    email on a meaningful move. Seams (run_audit, send_email) default to the
    real pipeline/transport but are injectable for tests.

    run_audit(url) -> { "overall": int, "scores": {category: int, ...} }
    send_email(to, subject, body) -> bool
    Returns {checked, audited, notified}.
    """
    now = now or datetime.now(timezone.utc)
    monitors = load_monitors(monitors_path)
    checked = audited = notified = 0

    for m in monitors:
        checked += 1
        if not is_due(m.get("last_audit_at"), m.get("frequency", "weekly"), now):
            continue

        result = await run_audit(m["url"]) if run_audit else None
        if not result:
            continue
        audited += 1

        prev_overall = m.get("last_overall")
        prev_scores = m.get("last_scores") or {}
        curr_overall = int(result.get("overall", 0))
        curr_scores = result.get("scores") or {}

        if should_notify(prev_overall, curr_overall):
            deltas = score_deltas(prev_scores, curr_scores)
            subject, body = build_delta_email(m["url"], int(prev_overall), curr_overall, deltas)
            if send_email and send_email(m["email"], subject, body):
                notified += 1

        # forward-stamp the monitor for the next cadence window
        m["last_audit_at"] = now.isoformat()
        m["last_overall"] = curr_overall
        m["last_scores"] = curr_scores

    save_monitors(monitors, monitors_path)
    return {"checked": checked, "audited": audited, "notified": notified}
