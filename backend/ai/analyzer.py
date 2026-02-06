"""
AI Analyzer - Uses Claude for intelligent analysis and price estimation
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime

from models.schemas import (
    AuditResult, AuditIssue, PriceEstimate, Severity
)


# Pricing constants (EUR/hour by complexity)
COMPLEXITY_MULTIPLIERS = {
    'simple': 1.0,
    'medium': 1.5,
    'complex': 2.5
}

# Severity urgency multipliers
SEVERITY_MULTIPLIERS = {
    'critical': 1.3,
    'high': 1.15,
    'medium': 1.0,
    'low': 0.9,
    'info': 0.8
}


async def generate_price_estimate(
    audit: AuditResult,
    hourly_rate: float,
    currency: str
) -> PriceEstimate:
    """Generate price estimate for fixing audit issues"""

    # Calculate hours by issue
    items = []
    hours_by_category = {}

    for issue in audit.issues:
        # Base hours from issue
        base_hours = issue.estimated_hours

        # Apply complexity multiplier
        complexity_mult = COMPLEXITY_MULTIPLIERS.get(issue.complexity, 1.0)

        # Apply severity multiplier
        severity_mult = SEVERITY_MULTIPLIERS.get(issue.severity.value, 1.0)

        # Calculate final hours
        final_hours = base_hours * complexity_mult * severity_mult

        # Add to category total
        category = issue.category.value
        hours_by_category[category] = hours_by_category.get(category, 0) + final_hours

        # Create line item
        items.append({
            'id': issue.id,
            'title': issue.title,
            'category': category,
            'severity': issue.severity.value,
            'complexity': issue.complexity,
            'base_hours': base_hours,
            'final_hours': round(final_hours, 1),
            'unit_price': round(final_hours * hourly_rate, 2)
        })

    # Calculate totals
    total_hours = sum(hours_by_category.values())

    # Apply volume discount
    if total_hours > 40:
        discount_percent = 15
    elif total_hours > 20:
        discount_percent = 10
    elif total_hours > 10:
        discount_percent = 5
    else:
        discount_percent = 0

    subtotal = total_hours * hourly_rate
    discount_amount = subtotal * (discount_percent / 100)
    total_price = subtotal - discount_amount

    # Count issues by severity
    issues_by_severity = {}
    for issue in audit.issues:
        sev = issue.severity.value
        issues_by_severity[sev] = issues_by_severity.get(sev, 0) + 1

    # Generate AI recommendations
    ai_analysis = await _get_ai_recommendations(audit, items)

    return PriceEstimate(
        audit_id=audit.id,
        total_issues=len(audit.issues),
        issues_by_severity=issues_by_severity,
        total_hours=round(total_hours, 1),
        hours_by_category={k: round(v, 1) for k, v in hours_by_category.items()},
        currency=currency,
        hourly_rate=hourly_rate,
        subtotal=round(subtotal, 2),
        discount_percent=discount_percent,
        total_price=round(total_price, 2),
        items=items,
        priority_order=ai_analysis.get('priority_order', []),
        quick_wins=ai_analysis.get('quick_wins', []),
        ai_summary=ai_analysis.get('summary', '')
    )


async def _get_ai_recommendations(
    audit: AuditResult,
    items: List[Dict]
) -> Dict[str, Any]:
    """Get AI-powered recommendations using Claude"""

    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        # Return default recommendations without AI
        return _get_default_recommendations(audit, items)

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Build issues summary
        issues_text = "\n".join([
            f"- [{item['severity'].upper()}] {item['title']} ({item['category']}, {item['final_hours']}h)"
            for item in items[:20]  # Limit to 20 for token efficiency
        ])

        prompt = f"""Analizează următoarele probleme găsite în auditul unui website și oferă recomandări:

URL auditat: {audit.url}
Scor general: {audit.overall_score}/100
Total probleme: {len(audit.issues)}

PROBLEME GĂSITE:
{issues_text}

INSTRUCȚIUNI:
1. Stabilește ordinea de prioritate pentru rezolvare (maximum 5 categorii)
2. Identifică "quick wins" - probleme ușor de rezolvat cu impact mare (maximum 5)
3. Scrie un rezumat executiv de 2-3 propoziții pentru client

Returnează DOAR un JSON valid cu această structură:
{{
    "priority_order": ["categoria1", "categoria2", ...],
    "quick_wins": ["titlu_problema1", "titlu_problema2", ...],
    "summary": "Rezumatul executiv aici..."
}}

Răspunde în română."""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Parse JSON from response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        return json.loads(response_text)

    except Exception as e:
        print(f"AI analysis failed: {e}")
        return _get_default_recommendations(audit, items)


def _get_default_recommendations(
    audit: AuditResult,
    items: List[Dict]
) -> Dict[str, Any]:
    """Generate default recommendations without AI"""

    # Sort items by severity and hours
    critical_items = [i for i in items if i['severity'] == 'critical']
    high_items = [i for i in items if i['severity'] == 'high']

    # Priority order by category with most critical issues
    category_severity = {}
    for item in items:
        cat = item['category']
        sev = item['severity']
        score = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0}[sev]
        category_severity[cat] = category_severity.get(cat, 0) + score

    priority_order = sorted(category_severity.keys(), key=lambda x: category_severity[x], reverse=True)

    # Quick wins: low hours, high severity
    quick_wins = [
        i['title'] for i in items
        if i['final_hours'] <= 1.0 and i['severity'] in ['critical', 'high']
    ][:5]

    # Generate summary
    if audit.overall_score >= 80:
        status = "Site-ul are un scor bun, cu câteva îmbunătățiri minore necesare."
    elif audit.overall_score >= 60:
        status = "Site-ul necesită atenție în mai multe arii pentru a atinge standarde optime."
    else:
        status = "Site-ul are probleme semnificative care necesită intervenție urgentă."

    critical_count = len(critical_items)
    high_count = len(high_items)

    summary = f"{status} Am identificat {critical_count} probleme critice și {high_count} probleme importante. Recomandăm să începeți cu problemele de securitate și GDPR pentru conformitate legală."

    return {
        'priority_order': priority_order[:5],
        'quick_wins': quick_wins,
        'summary': summary
    }


async def generate_audit_summary(audit: AuditResult) -> str:
    """Generate a human-readable audit summary"""

    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        return _get_default_summary(audit)

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        prompt = f"""Scrie un rezumat executiv pentru un audit de website.

URL: {audit.url}
Scor general: {audit.overall_score}/100
Scoruri pe categorii:
- Performance: {audit.performance_score or 'N/A'}/100
- SEO: {audit.seo_score or 'N/A'}/100
- Security: {audit.security_score or 'N/A'}/100
- GDPR: {audit.gdpr_score or 'N/A'}/100
- Accessibility: {audit.accessibility_score or 'N/A'}/100

Total probleme găsite: {len(audit.issues)}

Scrie un rezumat de maxim 150 cuvinte în română, destinat unui manager non-tehnic.
Menționează punctele forte și ariile care necesită atenție urgentă."""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    except Exception as e:
        print(f"AI summary generation failed: {e}")
        return _get_default_summary(audit)


def _get_default_summary(audit: AuditResult) -> str:
    """Generate default summary without AI"""

    score = audit.overall_score

    if score >= 80:
        rating = "foarte bun"
        recommendation = "menținerea standardelor actuale"
    elif score >= 60:
        rating = "satisfăcător"
        recommendation = "îmbunătățiri moderate"
    elif score >= 40:
        rating = "sub medie"
        recommendation = "intervenții semnificative"
    else:
        rating = "slab"
        recommendation = "măsuri urgente"

    return f"""Site-ul {audit.url} a obținut un scor general de {score}/100, considerat {rating}.

Au fost identificate {len(audit.issues)} probleme care necesită atenție. Recomandăm {recommendation} în ariile cu scoruri sub 70.

Detalii complete sunt disponibile în raportul complet."""
