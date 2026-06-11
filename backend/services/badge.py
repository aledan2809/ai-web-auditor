"""
Embeddable "Audited" badge — shields-style SVG with the overall score
(secondary roadmap item, test-tooling 2026-06-11). Site owners embed it on
their pages; every render is free marketing pointing back at the auditor.

Pure SVG string builder (unit-tested); the FastAPI route in main.py only does
the audit lookup + headers.
"""

BADGE_LABEL = "TechBiz Audit"


def score_color(score: int) -> str:
    """Green ≥80, amber ≥60, red below — same bands the report UI uses."""
    if score >= 80:
        return "#22c55e"
    if score >= 60:
        return "#f59e0b"
    return "#ef4444"


def build_badge_svg(score: int, label: str = BADGE_LABEL) -> str:
    """Two-segment shields-style badge: label | 'score ✓'."""
    score = max(0, min(100, int(score)))
    value = f"{score}/100 ✓"
    # ~6.1px per char at font-size 11 + padding — keeps widths stable without
    # measuring text (SVG has no layout engine server-side).
    label_w = int(len(label) * 6.1) + 14
    value_w = int(len(value) * 6.1) + 14
    total_w = label_w + value_w
    color = score_color(score)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" '
        f'role="img" aria-label="{label}: {value}">'
        f'<rect width="{label_w}" height="20" rx="3" fill="#1e293b"/>'
        f'<rect x="{label_w}" width="{value_w}" height="20" rx="3" fill="{color}"/>'
        f'<rect x="{label_w - 3}" width="3" height="20" fill="{color}"/>'
        f'<g font-family="Verdana,Geneva,sans-serif" font-size="11" fill="#fff" text-anchor="middle">'
        f'<text x="{label_w / 2:.0f}" y="14">{label}</text>'
        f'<text x="{label_w + value_w / 2:.0f}" y="14">{value}</text>'
        f'</g></svg>'
    )
