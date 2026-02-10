"""
AI Web Auditor — Scoring Service v1
Implements weighted component scoring with hard caps.
Reference: DEV_DECISIONS_v1.md §1, REPORT_CONTRACT_v1.md §2
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ── Component IDs (9 components, spec-aligned) ──────────────────────

class ComponentId(str, Enum):
    PERF  = "PERF"    # Performance / Core Web Vitals
    TSEO  = "TSEO"    # Technical SEO
    OPSEO = "OPSEO"   # On-page SEO
    SEC   = "SEC"     # Security
    PRIV  = "PRIV"    # Privacy / Compliance
    A11Y  = "A11Y"    # Accessibility
    MOBUX = "MOBUX"    # Mobile UX
    TRUST = "TRUST"   # Trust & Conversions
    COMP  = "COMP"    # Competitor Gap


# ── Component weights (UAE SMB default, sum = 1.0) ──────────────────

COMPONENT_WEIGHTS: Dict[ComponentId, float] = {
    ComponentId.PERF:  0.20,
    ComponentId.OPSEO: 0.15,
    ComponentId.TSEO:  0.10,
    ComponentId.MOBUX: 0.10,
    ComponentId.SEC:   0.10,
    ComponentId.TRUST: 0.10,
    ComponentId.PRIV:  0.10,
    ComponentId.A11Y:  0.05,
    ComponentId.COMP:  0.10,
}

# Sanity check
assert abs(sum(COMPONENT_WEIGHTS.values()) - 1.0) < 0.001, "Component weights must sum to 1.0"


# ── Status labels ────────────────────────────────────────────────────

def score_status(score: int) -> str:
    """Return human-readable status label for a score 0-100."""
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 55:
        return "Warning"
    return "Fail"


# ── Check result ─────────────────────────────────────────────────────

class CheckResult(str, Enum):
    PASS    = "PASS"
    PARTIAL = "PARTIAL"
    FAIL    = "FAIL"


@dataclass
class CheckOutcome:
    """Result of a single audit check."""
    check_id: str
    component_id: ComponentId
    result: CheckResult
    severity_weight: int = 3          # 1-5, default 3
    confidence: float = 0.85          # 0-1
    evidence_url: Optional[str] = None
    evidence_detail: Optional[str] = None

    @property
    def fail_factor(self) -> float:
        if self.result == CheckResult.PASS:
            return 0.0
        if self.result == CheckResult.PARTIAL:
            return 0.5
        return 1.0  # FAIL

    @property
    def penalty(self) -> float:
        return self.severity_weight * self.confidence * self.fail_factor


# ── Component score ──────────────────────────────────────────────────

@dataclass
class ComponentScore:
    component_id: ComponentId
    score: int                            # 0-100
    status: str                           # Excellent / Good / Warning / Fail
    checks: List[CheckOutcome] = field(default_factory=list)
    hard_cap_applied: Optional[str] = None  # reason if capped


def compute_component_score(
    component_id: ComponentId,
    checks: List[CheckOutcome],
) -> ComponentScore:
    """
    Compute score for a single component.
    Formula: score = max(0, 100 - 100 * (sum(penalty) / max_penalty))
    """
    if not checks:
        return ComponentScore(
            component_id=component_id,
            score=100,
            status="Excellent",
            checks=[],
        )

    total_penalty = sum(c.penalty for c in checks)
    max_penalty = sum(c.severity_weight for c in checks)

    if max_penalty == 0:
        raw_score = 100
    else:
        raw_score = max(0, 100 - 100 * (total_penalty / max_penalty))

    score = round(raw_score)

    return ComponentScore(
        component_id=component_id,
        score=score,
        status=score_status(score),
        checks=checks,
    )


# ── Hard caps (REPORT_CONTRACT_v1.md §2.4) ──────────────────────────

@dataclass
class HardCap:
    condition: str
    component_cap: Optional[tuple] = None  # (ComponentId, max_score)
    overall_cap: Optional[int] = None


def detect_hard_caps(component_scores: Dict[ComponentId, ComponentScore]) -> List[HardCap]:
    """Detect which hard caps should be applied based on check results."""
    caps: List[HardCap] = []

    # Helper: check if a specific check_id FAILed in a component
    def check_failed(comp_id: ComponentId, check_id: str) -> bool:
        cs = component_scores.get(comp_id)
        if not cs:
            return False
        return any(
            c.check_id == check_id and c.result == CheckResult.FAIL
            for c in cs.checks
        )

    # No HTTPS → SEC cap 40, overall cap 60
    if check_failed(ComponentId.SEC, "SEC-01") or check_failed(ComponentId.SEC, "SEC-HTTPS-001"):
        caps.append(HardCap(
            condition="No HTTPS",
            component_cap=(ComponentId.SEC, 40),
            overall_cap=60,
        ))

    # No Privacy Policy + trackers → PRIV cap 50
    priv_cs = component_scores.get(ComponentId.PRIV)
    if priv_cs:
        policy_missing = any(
            c.check_id in ("PRIV-01", "PRIV-POLICY-001") and c.result == CheckResult.FAIL
            for c in priv_cs.checks
        )
        trackers_present = any(
            c.check_id in ("PRIV-02", "PRIV-COOKIES-002", "PRIV-CONSENT-003")
            and c.result == CheckResult.FAIL
            for c in priv_cs.checks
        )
        if policy_missing and trackers_present:
            caps.append(HardCap(
                condition="No Privacy Policy + trackers detected",
                component_cap=(ComponentId.PRIV, 50),
                overall_cap=None,
            ))

    # Site-wide noindex → TSEO cap 30, overall cap 50
    if check_failed(ComponentId.TSEO, "TSEO-01") or check_failed(ComponentId.TSEO, "TSEO-NOINDEX-001"):
        caps.append(HardCap(
            condition="Site-wide noindex",
            component_cap=(ComponentId.TSEO, 30),
            overall_cap=50,
        ))

    return caps


def apply_hard_caps(
    component_scores: Dict[ComponentId, ComponentScore],
    caps: List[HardCap],
) -> Dict[ComponentId, ComponentScore]:
    """Apply hard caps in-place and annotate."""
    for cap in caps:
        if cap.component_cap:
            comp_id, max_score = cap.component_cap
            cs = component_scores.get(comp_id)
            if cs and cs.score > max_score:
                cs.score = max_score
                cs.status = score_status(max_score)
                cs.hard_cap_applied = cap.condition
    return component_scores


# ── Overall score ────────────────────────────────────────────────────

@dataclass
class OverallResult:
    overall_score: int
    overall_status: str
    component_scores: Dict[ComponentId, ComponentScore]
    hard_caps_applied: List[str]
    top_risks: List[dict]
    top_quick_wins: List[dict]


def compute_overall_score(
    component_scores: Dict[ComponentId, ComponentScore],
    weights: Optional[Dict[ComponentId, float]] = None,
) -> OverallResult:
    """
    Compute weighted overall score with hard caps.
    Returns OverallResult with component breakdown.
    """
    if weights is None:
        weights = COMPONENT_WEIGHTS

    # 1) Detect and apply hard caps
    caps = detect_hard_caps(component_scores)
    component_scores = apply_hard_caps(component_scores, caps)

    # 2) Weighted sum
    weighted_sum = 0.0
    weight_used = 0.0

    for comp_id, weight in weights.items():
        cs = component_scores.get(comp_id)
        if cs is not None:
            weighted_sum += cs.score * weight
            weight_used += weight

    # Normalize if some components are missing
    if weight_used > 0:
        raw_overall = weighted_sum / weight_used * sum(weights.values())
        # Simplify: if all present, raw_overall = weighted_sum
        raw_overall = weighted_sum if abs(weight_used - sum(weights.values())) < 0.001 else (weighted_sum / weight_used)
    else:
        raw_overall = 0

    # 3) Apply overall hard caps
    overall_cap = min(
        (cap.overall_cap for cap in caps if cap.overall_cap is not None),
        default=100,
    )
    final_score = min(round(raw_overall), overall_cap)

    # 4) Collect top risks (CRITICAL/HIGH issues with lowest scores)
    all_checks: List[CheckOutcome] = []
    for cs in component_scores.values():
        all_checks.extend(cs.checks)

    failed_checks = [
        c for c in all_checks
        if c.result in (CheckResult.FAIL, CheckResult.PARTIAL)
    ]
    failed_checks.sort(key=lambda c: (-c.severity_weight, -c.penalty))

    top_risks = [
        {"issueId": c.check_id, "severity": _severity_label(c.severity_weight)}
        for c in failed_checks[:5]
    ]

    # 5) Quick wins: high impact, fixable
    quick_wins = [
        {"issueId": c.check_id, "expectedImpact": f"Improves {c.component_id.value}"}
        for c in failed_checks
        if c.severity_weight >= 3 and c.confidence >= 0.7
    ][:5]

    return OverallResult(
        overall_score=final_score,
        overall_status=score_status(final_score),
        component_scores=component_scores,
        hard_caps_applied=[cap.condition for cap in caps],
        top_risks=top_risks,
        top_quick_wins=quick_wins,
    )


def _severity_label(weight: int) -> str:
    """Map severity_weight (1-5) to label."""
    if weight >= 5:
        return "CRITICAL"
    if weight >= 4:
        return "HIGH"
    if weight >= 3:
        return "MEDIUM"
    return "LOW"


# ── Adapter: convert legacy auditor scores to ComponentScore ─────────

def from_legacy_scores(
    performance_score: Optional[int] = None,
    seo_score: Optional[int] = None,
    security_score: Optional[int] = None,
    gdpr_score: Optional[int] = None,
    accessibility_score: Optional[int] = None,
    mobile_ux_score: Optional[int] = None,
    trust_score: Optional[int] = None,
    competitor_score: Optional[int] = None,
    tseo_score: Optional[int] = None,
    opseo_score: Optional[int] = None,
) -> Dict[ComponentId, ComponentScore]:
    """
    Bridge auditor scores to the 9-component model.

    Mapping:
    - performance_score → PERF
    - tseo_score / opseo_score → TSEO / OPSEO (preferred)
    - seo_score → fallback: split equally to TSEO + OPSEO
    - security_score → SEC
    - gdpr_score → PRIV
    - accessibility_score → A11Y
    - mobile_ux_score → MOBUX
    - trust_score → TRUST
    - competitor_score → COMP
    """
    scores: Dict[ComponentId, ComponentScore] = {}

    if performance_score is not None:
        scores[ComponentId.PERF] = ComponentScore(
            component_id=ComponentId.PERF,
            score=performance_score,
            status=score_status(performance_score),
        )

    # Use split TSEO/OPSEO if available, fallback to combined seo_score
    _tseo = tseo_score if tseo_score is not None else seo_score
    _opseo = opseo_score if opseo_score is not None else seo_score

    if _tseo is not None:
        scores[ComponentId.TSEO] = ComponentScore(
            component_id=ComponentId.TSEO,
            score=_tseo,
            status=score_status(_tseo),
        )
    if _opseo is not None:
        scores[ComponentId.OPSEO] = ComponentScore(
            component_id=ComponentId.OPSEO,
            score=_opseo,
            status=score_status(_opseo),
        )

    if security_score is not None:
        scores[ComponentId.SEC] = ComponentScore(
            component_id=ComponentId.SEC,
            score=security_score,
            status=score_status(security_score),
        )

    if gdpr_score is not None:
        scores[ComponentId.PRIV] = ComponentScore(
            component_id=ComponentId.PRIV,
            score=gdpr_score,
            status=score_status(gdpr_score),
        )

    if accessibility_score is not None:
        scores[ComponentId.A11Y] = ComponentScore(
            component_id=ComponentId.A11Y,
            score=accessibility_score,
            status=score_status(accessibility_score),
        )

    if mobile_ux_score is not None:
        scores[ComponentId.MOBUX] = ComponentScore(
            component_id=ComponentId.MOBUX,
            score=mobile_ux_score,
            status=score_status(mobile_ux_score),
        )

    if trust_score is not None:
        scores[ComponentId.TRUST] = ComponentScore(
            component_id=ComponentId.TRUST,
            score=trust_score,
            status=score_status(trust_score),
        )

    if competitor_score is not None:
        scores[ComponentId.COMP] = ComponentScore(
            component_id=ComponentId.COMP,
            score=competitor_score,
            status=score_status(competitor_score),
        )

    return scores


# ── Serialize for API response ───────────────────────────────────────

def overall_result_to_dict(result: OverallResult) -> dict:
    """Convert OverallResult to JSON-serializable dict (API response)."""
    return {
        "overallScore": result.overall_score,
        "overallStatus": result.overall_status,
        "hardCapsApplied": result.hard_caps_applied,
        "topRisks": result.top_risks,
        "topQuickWins": result.top_quick_wins,
        "components": [
            {
                "componentId": cs.component_id.value,
                "name": _component_name(cs.component_id),
                "score": cs.score,
                "status": cs.status,
                "hardCapApplied": cs.hard_cap_applied,
                "checks": [
                    {
                        "checkId": ch.check_id,
                        "result": ch.result.value,
                        "severityWeight": ch.severity_weight,
                        "confidence": ch.confidence,
                    }
                    for ch in cs.checks
                ],
            }
            for cs in result.component_scores.values()
        ],
    }


def _component_name(cid: ComponentId) -> str:
    """Human-readable component name."""
    return {
        ComponentId.PERF:  "Core Web Vitals",
        ComponentId.TSEO:  "Technical SEO",
        ComponentId.OPSEO: "On-Page SEO",
        ComponentId.SEC:   "Security",
        ComponentId.PRIV:  "Privacy & Compliance",
        ComponentId.A11Y:  "Accessibility",
        ComponentId.MOBUX: "Mobile UX",
        ComponentId.TRUST: "Trust & Conversions",
        ComponentId.COMP:  "Competitor Gap",
    }.get(cid, cid.value)
