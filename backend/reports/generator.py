"""
PDF Report Generator - Creates professional, comprehensive audit reports
Supports Romanian (ro) and English (en) languages

Features:
- Executive summary with visual score
- Category breakdown with screenshots
- Score justification and argumentation
- Detailed issues with examples
- Estimated time per fix
- Priority action plan
- Website Guru CTA
"""

import os
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import io
import asyncio

from models.schemas import AuditResult, AuditIssue, Severity, AuditType
from translations import t


# ============================================================================
# TRANSLATIONS FOR ENHANCED REPORT
# ============================================================================
REPORT_TRANSLATIONS = {
    "ro": {
        # Executive Summary
        "executive_summary": "REZUMAT EXECUTIV",
        "site_analyzed": "Site analizat",
        "analysis_date": "Data analizei",
        "your_score": "Scorul tau",

        # Score interpretations
        "score_interpretation": "Interpretare Scor",
        "score_90_100": "Excelent! Site-ul tau respecta cele mai bune practici din industrie.",
        "score_80_89": "Foarte bun! Cateva imbunatatiri minore pot perfectiona site-ul.",
        "score_70_79": "Bun, dar exista oportunitati importante de optimizare.",
        "score_60_69": "Satisfacator. Recomandam atentie la problemele identificate.",
        "score_40_59": "Necesita imbunatatiri semnificative pentru a fi competitiv.",
        "score_0_39": "Probleme critice care afecteaza experienta utilizatorilor si SEO.",

        # Category sections
        "category_analysis": "ANALIZA PE CATEGORII",
        "why_matters": "De ce conteaza",
        "current_status": "Stare curenta",
        "key_findings": "Constatari cheie",
        "score_justification": "Justificare scor",

        # Category explanations
        "perf_why": "Viteza de incarcare afecteaza direct rata de conversie. Google indica ca 53% din utilizatorii mobile abandoneaza un site care se incarca in mai mult de 3 secunde.",
        "seo_why": "Optimizarea pentru motoarele de cautare determina vizibilitatea organica. 68% din experienta online incepe cu o cautare.",
        "sec_why": "Securitatea protejeaza datele utilizatorilor si credibilitatea brandului. 85% din utilizatori nu vor cumpara de pe un site nesigur.",
        "gdpr_why": "Conformitatea GDPR evita amenzi de pana la 4% din cifra de afaceri anuala si construieste incredere cu clientii.",
        "a11y_why": "Accesibilitatea asigura ca 15% din populatie (persoane cu dizabilitati) poate accesa site-ul tau.",

        # Issues section
        "detailed_issues": "PROBLEME DETALIATE",
        "issue_number": "Problema",
        "problem": "Problema",
        "impact": "Impact",
        "solution": "Solutie",
        "example": "Exemplu",
        "time_to_fix": "Timp estimat",
        "difficulty": "Dificultate",

        # Difficulty levels
        "diff_simple": "Usor (poate fi facut de oricine)",
        "diff_medium": "Mediu (necesita cunostinte tehnice)",
        "diff_complex": "Complex (necesita dezvoltator experimentat)",

        # Impact levels
        "impact_critical": "Critic - afecteaza major experienta si pozitionarea",
        "impact_high": "Important - imbunatatire semnificativa dupa rezolvare",
        "impact_medium": "Moderat - contribuie la scorul general",
        "impact_low": "Minor - recomandare pentru perfectiune",

        # Action plan
        "action_plan": "PLAN DE ACTIUNE PRIORITIZAT",
        "quick_wins": "Castiguri Rapide (sub 2 ore)",
        "quick_wins_desc": "Aceste probleme pot fi rezolvate rapid cu impact mare:",
        "medium_effort": "Efort Mediu (2-8 ore)",
        "major_changes": "Schimbari Majore (8+ ore)",

        # Summary
        "total_summary": "SUMAR TOTAL",
        "total_issues": "Total probleme identificate",
        "critical_issues": "Probleme critice",
        "total_time": "Timp total estimat",
        "hours": "ore",
        "estimated_cost": "Cost estimat implementare",

        # CTA Section
        "need_help": "AI NEVOIE DE AJUTOR?",
        "cta_title": "Lasa-ne sa rezolvam problemele pentru tine!",
        "cta_desc": "Echipa Website Guru poate implementa toate recomandarile din acest raport.",
        "cta_benefits": [
            "Implementare profesionala garantata",
            "Raport de progres saptamanal",
            "Suport continuu 6 luni",
            "Garantie de imbunatatire scor"
        ],
        "cta_link": "Solicita oferta personalizata:",
        "cta_url": "https://websiteguru.ro/contact?ref=audit",

        # Footer
        "report_footer": "Raport generat de AI Web Auditor",
        "confidential": "Document confidential - Numai pentru uz intern",
        "page": "Pagina",

        # Screenshots
        "desktop_view": "Vizualizare Desktop",
        "mobile_view": "Vizualizare Mobil",
        "screenshot_analysis": "Analiza Vizuala",
    },
    "en": {
        # Executive Summary
        "executive_summary": "EXECUTIVE SUMMARY",
        "site_analyzed": "Site analyzed",
        "analysis_date": "Analysis date",
        "your_score": "Your score",

        # Score interpretations
        "score_interpretation": "Score Interpretation",
        "score_90_100": "Excellent! Your site follows industry best practices.",
        "score_80_89": "Very good! A few minor improvements can perfect your site.",
        "score_70_79": "Good, but there are important optimization opportunities.",
        "score_60_69": "Satisfactory. We recommend attention to identified issues.",
        "score_40_59": "Needs significant improvements to be competitive.",
        "score_0_39": "Critical issues affecting user experience and SEO.",

        # Category sections
        "category_analysis": "CATEGORY ANALYSIS",
        "why_matters": "Why it matters",
        "current_status": "Current status",
        "key_findings": "Key findings",
        "score_justification": "Score justification",

        # Category explanations
        "perf_why": "Loading speed directly affects conversion rate. Google indicates that 53% of mobile users abandon a site that takes more than 3 seconds to load.",
        "seo_why": "Search engine optimization determines organic visibility. 68% of online experiences begin with a search.",
        "sec_why": "Security protects user data and brand credibility. 85% of users will not buy from an insecure site.",
        "gdpr_why": "GDPR compliance avoids fines of up to 4% of annual turnover and builds trust with customers.",
        "a11y_why": "Accessibility ensures that 15% of the population (people with disabilities) can access your site.",

        # Issues section
        "detailed_issues": "DETAILED ISSUES",
        "issue_number": "Issue",
        "problem": "Problem",
        "impact": "Impact",
        "solution": "Solution",
        "example": "Example",
        "time_to_fix": "Estimated time",
        "difficulty": "Difficulty",

        # Difficulty levels
        "diff_simple": "Easy (can be done by anyone)",
        "diff_medium": "Medium (requires technical knowledge)",
        "diff_complex": "Complex (requires experienced developer)",

        # Impact levels
        "impact_critical": "Critical - majorly affects experience and ranking",
        "impact_high": "Important - significant improvement after resolution",
        "impact_medium": "Moderate - contributes to overall score",
        "impact_low": "Minor - recommendation for perfection",

        # Action plan
        "action_plan": "PRIORITIZED ACTION PLAN",
        "quick_wins": "Quick Wins (under 2 hours)",
        "quick_wins_desc": "These issues can be resolved quickly with high impact:",
        "medium_effort": "Medium Effort (2-8 hours)",
        "major_changes": "Major Changes (8+ hours)",

        # Summary
        "total_summary": "TOTAL SUMMARY",
        "total_issues": "Total issues identified",
        "critical_issues": "Critical issues",
        "total_time": "Total estimated time",
        "hours": "hours",
        "estimated_cost": "Estimated implementation cost",

        # CTA Section
        "need_help": "NEED HELP?",
        "cta_title": "Let us fix the issues for you!",
        "cta_desc": "The Website Guru team can implement all recommendations from this report.",
        "cta_benefits": [
            "Guaranteed professional implementation",
            "Weekly progress report",
            "6 months continuous support",
            "Score improvement guarantee"
        ],
        "cta_link": "Request personalized quote:",
        "cta_url": "https://websiteguru.ro/contact?ref=audit",

        # Footer
        "report_footer": "Report generated by AI Web Auditor",
        "confidential": "Confidential document - For internal use only",
        "page": "Page",

        # Screenshots
        "desktop_view": "Desktop View",
        "mobile_view": "Mobile View",
        "screenshot_analysis": "Visual Analysis",
    }
}


def rt(key: str, lang: str = "ro") -> Any:
    """Get report translation"""
    translations = REPORT_TRANSLATIONS.get(lang, REPORT_TRANSLATIONS["en"])
    return translations.get(key, key)


# ============================================================================
# SCORE JUSTIFICATION GENERATOR
# ============================================================================
def generate_score_justification(category: str, score: int, metrics: Any, issues: List[AuditIssue], lang: str = "ro") -> str:
    """Generate detailed score justification based on metrics and issues"""

    justifications = {
        "performance": {
            "ro": _justify_performance_ro,
            "en": _justify_performance_en
        },
        "seo": {
            "ro": _justify_seo_ro,
            "en": _justify_seo_en
        },
        "security": {
            "ro": _justify_security_ro,
            "en": _justify_security_en
        },
        "gdpr": {
            "ro": _justify_gdpr_ro,
            "en": _justify_gdpr_en
        },
        "accessibility": {
            "ro": _justify_accessibility_ro,
            "en": _justify_accessibility_en
        }
    }

    func = justifications.get(category, {}).get(lang)
    if func and metrics:
        return func(score, metrics, issues)

    # Default justification
    if lang == "ro":
        return f"Scorul de {score}/100 reflecta starea actuala a site-ului in aceasta categorie."
    return f"The score of {score}/100 reflects the current state of the site in this category."


def _justify_performance_ro(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"Scorul de {score}/100 se bazeaza pe urmatoarele metrici Core Web Vitals:")

    if hasattr(metrics, 'lcp'):
        lcp_status = "bun" if metrics.lcp <= 2.5 else ("necesita imbunatatire" if metrics.lcp <= 4 else "slab")
        parts.append(f"- LCP (Largest Contentful Paint): {metrics.lcp:.1f}s ({lcp_status}) - masoara viteza de incarcare a continutului principal")

    if hasattr(metrics, 'fid'):
        fid_status = "bun" if metrics.fid <= 100 else ("necesita imbunatatire" if metrics.fid <= 300 else "slab")
        parts.append(f"- FID (First Input Delay): {metrics.fid:.0f}ms ({fid_status}) - masoara interactivitatea")

    if hasattr(metrics, 'cls'):
        cls_status = "bun" if metrics.cls <= 0.1 else ("necesita imbunatatire" if metrics.cls <= 0.25 else "slab")
        parts.append(f"- CLS (Cumulative Layout Shift): {metrics.cls:.2f} ({cls_status}) - masoara stabilitatea vizuala")

    critical_count = len([i for i in issues if i.category == AuditType.PERFORMANCE and i.severity == Severity.CRITICAL])
    if critical_count > 0:
        parts.append(f"\nAu fost identificate {critical_count} probleme critice care afecteaza semnificativ scorul.")

    return "\n".join(parts)


def _justify_performance_en(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"The score of {score}/100 is based on the following Core Web Vitals metrics:")

    if hasattr(metrics, 'lcp'):
        lcp_status = "good" if metrics.lcp <= 2.5 else ("needs improvement" if metrics.lcp <= 4 else "poor")
        parts.append(f"- LCP (Largest Contentful Paint): {metrics.lcp:.1f}s ({lcp_status}) - measures main content loading speed")

    if hasattr(metrics, 'fid'):
        fid_status = "good" if metrics.fid <= 100 else ("needs improvement" if metrics.fid <= 300 else "poor")
        parts.append(f"- FID (First Input Delay): {metrics.fid:.0f}ms ({fid_status}) - measures interactivity")

    if hasattr(metrics, 'cls'):
        cls_status = "good" if metrics.cls <= 0.1 else ("needs improvement" if metrics.cls <= 0.25 else "poor")
        parts.append(f"- CLS (Cumulative Layout Shift): {metrics.cls:.2f} ({cls_status}) - measures visual stability")

    critical_count = len([i for i in issues if i.category == AuditType.PERFORMANCE and i.severity == Severity.CRITICAL])
    if critical_count > 0:
        parts.append(f"\n{critical_count} critical issues were identified that significantly affect the score.")

    return "\n".join(parts)


def _justify_seo_ro(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"Scorul SEO de {score}/100 reflecta:")

    if hasattr(metrics, 'title') and metrics.title:
        parts.append(f"+ Title tag prezent ({metrics.title_length} caractere)")
    else:
        parts.append("- Title tag lipsa (impact major)")

    if hasattr(metrics, 'meta_description') and metrics.meta_description:
        parts.append(f"+ Meta description prezenta ({metrics.meta_description_length} caractere)")
    else:
        parts.append("- Meta description lipsa")

    if hasattr(metrics, 'h1_count'):
        if metrics.h1_count == 1:
            parts.append("+ Structura H1 corecta")
        elif metrics.h1_count == 0:
            parts.append("- Lipsa tag H1")
        else:
            parts.append(f"- Multiple H1 ({metrics.h1_count}) - nerecomandat")

    if hasattr(metrics, 'robots_txt_exists'):
        parts.append(f"{'+ ' if metrics.robots_txt_exists else '- '}robots.txt {'prezent' if metrics.robots_txt_exists else 'lipsa'}")

    if hasattr(metrics, 'sitemap_exists'):
        parts.append(f"{'+ ' if metrics.sitemap_exists else '- '}sitemap.xml {'prezent' if metrics.sitemap_exists else 'lipsa'}")

    return "\n".join(parts)


def _justify_seo_en(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"The SEO score of {score}/100 reflects:")

    if hasattr(metrics, 'title') and metrics.title:
        parts.append(f"+ Title tag present ({metrics.title_length} characters)")
    else:
        parts.append("- Title tag missing (major impact)")

    if hasattr(metrics, 'meta_description') and metrics.meta_description:
        parts.append(f"+ Meta description present ({metrics.meta_description_length} characters)")
    else:
        parts.append("- Meta description missing")

    if hasattr(metrics, 'h1_count'):
        if metrics.h1_count == 1:
            parts.append("+ Correct H1 structure")
        elif metrics.h1_count == 0:
            parts.append("- H1 tag missing")
        else:
            parts.append(f"- Multiple H1 ({metrics.h1_count}) - not recommended")

    if hasattr(metrics, 'robots_txt_exists'):
        parts.append(f"{'+ ' if metrics.robots_txt_exists else '- '}robots.txt {'present' if metrics.robots_txt_exists else 'missing'}")

    if hasattr(metrics, 'sitemap_exists'):
        parts.append(f"{'+ ' if metrics.sitemap_exists else '- '}sitemap.xml {'present' if metrics.sitemap_exists else 'missing'}")

    return "\n".join(parts)


def _justify_security_ro(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"Scorul de securitate de {score}/100 se bazeaza pe:")

    if hasattr(metrics, 'https_enabled'):
        parts.append(f"{'+ ' if metrics.https_enabled else '- '}HTTPS {'activ' if metrics.https_enabled else 'inactiv (critic!)'}")

    if hasattr(metrics, 'ssl_valid'):
        parts.append(f"{'+ ' if metrics.ssl_valid else '- '}Certificat SSL {'valid' if metrics.ssl_valid else 'invalid sau expirat'}")

    if hasattr(metrics, 'hsts_enabled'):
        parts.append(f"{'+ ' if metrics.hsts_enabled else '- '}HSTS {'configurat' if metrics.hsts_enabled else 'lipsa'}")

    if hasattr(metrics, 'csp_enabled'):
        parts.append(f"{'+ ' if metrics.csp_enabled else '- '}Content Security Policy {'activa' if metrics.csp_enabled else 'lipsa'}")

    if hasattr(metrics, 'x_frame_options'):
        parts.append(f"{'+ ' if metrics.x_frame_options else '- '}X-Frame-Options {'configurat' if metrics.x_frame_options else 'lipsa'}")

    return "\n".join(parts)


def _justify_security_en(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"The security score of {score}/100 is based on:")

    if hasattr(metrics, 'https_enabled'):
        parts.append(f"{'+ ' if metrics.https_enabled else '- '}HTTPS {'enabled' if metrics.https_enabled else 'disabled (critical!)'}")

    if hasattr(metrics, 'ssl_valid'):
        parts.append(f"{'+ ' if metrics.ssl_valid else '- '}SSL Certificate {'valid' if metrics.ssl_valid else 'invalid or expired'}")

    if hasattr(metrics, 'hsts_enabled'):
        parts.append(f"{'+ ' if metrics.hsts_enabled else '- '}HSTS {'configured' if metrics.hsts_enabled else 'missing'}")

    if hasattr(metrics, 'csp_enabled'):
        parts.append(f"{'+ ' if metrics.csp_enabled else '- '}Content Security Policy {'active' if metrics.csp_enabled else 'missing'}")

    if hasattr(metrics, 'x_frame_options'):
        parts.append(f"{'+ ' if metrics.x_frame_options else '- '}X-Frame-Options {'configured' if metrics.x_frame_options else 'missing'}")

    return "\n".join(parts)


def _justify_gdpr_ro(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"Scorul GDPR de {score}/100 reflecta conformitatea cu regulamentul:")

    if hasattr(metrics, 'cookie_banner_present'):
        parts.append(f"{'+ ' if metrics.cookie_banner_present else '- '}Banner cookie {'prezent' if metrics.cookie_banner_present else 'lipsa (obligatoriu!)'}")

    if hasattr(metrics, 'privacy_policy_link'):
        parts.append(f"{'+ ' if metrics.privacy_policy_link else '- '}Politica confidentialitate {'vizibila' if metrics.privacy_policy_link else 'lipsa'}")

    if hasattr(metrics, 'opt_out_option'):
        parts.append(f"{'+ ' if metrics.opt_out_option else '- '}Optiune refuz cookie-uri {'disponibila' if metrics.opt_out_option else 'lipsa'}")

    if hasattr(metrics, 'third_party_trackers') and metrics.third_party_trackers:
        parts.append(f"! {len(metrics.third_party_trackers)} trackere terte detectate")

    return "\n".join(parts)


def _justify_gdpr_en(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"The GDPR score of {score}/100 reflects compliance with the regulation:")

    if hasattr(metrics, 'cookie_banner_present'):
        parts.append(f"{'+ ' if metrics.cookie_banner_present else '- '}Cookie banner {'present' if metrics.cookie_banner_present else 'missing (required!)'}")

    if hasattr(metrics, 'privacy_policy_link'):
        parts.append(f"{'+ ' if metrics.privacy_policy_link else '- '}Privacy policy {'visible' if metrics.privacy_policy_link else 'missing'}")

    if hasattr(metrics, 'opt_out_option'):
        parts.append(f"{'+ ' if metrics.opt_out_option else '- '}Cookie opt-out option {'available' if metrics.opt_out_option else 'missing'}")

    if hasattr(metrics, 'third_party_trackers') and metrics.third_party_trackers:
        parts.append(f"! {len(metrics.third_party_trackers)} third-party trackers detected")

    return "\n".join(parts)


def _justify_accessibility_ro(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"Scorul de accesibilitate de {score}/100 (standard WCAG {getattr(metrics, 'wcag_level', 'AA')}):")

    if hasattr(metrics, 'color_contrast_issues'):
        if metrics.color_contrast_issues == 0:
            parts.append("+ Contrast culori corespunzator")
        else:
            parts.append(f"- {metrics.color_contrast_issues} probleme de contrast")

    if hasattr(metrics, 'missing_alt_texts'):
        if metrics.missing_alt_texts == 0:
            parts.append("+ Toate imaginile au text alt")
        else:
            parts.append(f"- {metrics.missing_alt_texts} imagini fara text alt")

    if hasattr(metrics, 'missing_form_labels'):
        if metrics.missing_form_labels == 0:
            parts.append("+ Formulare etichetate corect")
        else:
            parts.append(f"- {metrics.missing_form_labels} campuri fara etichete")

    if hasattr(metrics, 'keyboard_navigation'):
        parts.append(f"{'+ ' if metrics.keyboard_navigation else '- '}Navigare tastatura {'functionala' if metrics.keyboard_navigation else 'problematica'}")

    return "\n".join(parts)


def _justify_accessibility_en(score: int, metrics, issues: List[AuditIssue]) -> str:
    parts = []
    parts.append(f"The accessibility score of {score}/100 (WCAG {getattr(metrics, 'wcag_level', 'AA')} standard):")

    if hasattr(metrics, 'color_contrast_issues'):
        if metrics.color_contrast_issues == 0:
            parts.append("+ Color contrast adequate")
        else:
            parts.append(f"- {metrics.color_contrast_issues} contrast issues")

    if hasattr(metrics, 'missing_alt_texts'):
        if metrics.missing_alt_texts == 0:
            parts.append("+ All images have alt text")
        else:
            parts.append(f"- {metrics.missing_alt_texts} images without alt text")

    if hasattr(metrics, 'missing_form_labels'):
        if metrics.missing_form_labels == 0:
            parts.append("+ Forms properly labeled")
        else:
            parts.append(f"- {metrics.missing_form_labels} fields without labels")

    if hasattr(metrics, 'keyboard_navigation'):
        parts.append(f"{'+ ' if metrics.keyboard_navigation else '- '}Keyboard navigation {'functional' if metrics.keyboard_navigation else 'problematic'}")

    return "\n".join(parts)


# ============================================================================
# MAIN PDF GENERATOR
# ============================================================================
async def generate_pdf_report(audit: AuditResult, lang: str = "ro") -> str:
    """Generate a comprehensive PDF report from audit results"""

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image, ListFlowable, ListItem, KeepTogether,
            HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.graphics.shapes import Drawing, Rect, String, Circle
        from reportlab.graphics.charts.piecharts import Pie
    except ImportError:
        return await _generate_simple_report(audit, lang)

    # Create output directory
    output_dir = Path(__file__).parent.parent / 'data' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"audit_report_{audit.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    filepath = output_dir / filename

    # Create PDF with custom page numbers
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Define all styles
    styles = _create_styles()

    # Build content
    content = []

    # =========================================================================
    # PAGE 1: COVER PAGE & EXECUTIVE SUMMARY
    # =========================================================================
    content.extend(_build_cover_page(audit, styles, lang))
    content.append(PageBreak())

    # =========================================================================
    # PAGE 2-3: CATEGORY ANALYSIS WITH SCREENSHOTS
    # =========================================================================
    content.extend(_build_category_analysis(audit, styles, lang))
    content.append(PageBreak())

    # =========================================================================
    # PAGE 4+: DETAILED ISSUES
    # =========================================================================
    content.extend(_build_detailed_issues(audit, styles, lang))
    content.append(PageBreak())

    # =========================================================================
    # ACTION PLAN
    # =========================================================================
    content.extend(_build_action_plan(audit, styles, lang))
    content.append(PageBreak())

    # =========================================================================
    # FINAL PAGE: SUMMARY & CTA
    # =========================================================================
    content.extend(_build_summary_and_cta(audit, styles, lang))

    # Build PDF
    doc.build(content)

    return str(filepath)


def _create_styles():
    """Create all paragraph styles for the report"""
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

    styles = getSampleStyleSheet()

    # Title styles
    styles.add(ParagraphStyle(
        name='CoverTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a365d')
    ))

    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#4a5568'),
        alignment=TA_CENTER,
        spaceAfter=20
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=15,
        textColor=colors.HexColor('#1a365d'),
        borderColor=colors.HexColor('#3182ce'),
        borderWidth=0,
        borderPadding=5
    ))

    styles.add(ParagraphStyle(
        name='SubsectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#2d3748')
    ))

    # Override built-in BodyText (already exists in default stylesheet)
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].alignment = TA_JUSTIFY
    styles['BodyText'].textColor = colors.HexColor('#4a5568')

    styles.add(ParagraphStyle(
        name='SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096')
    ))

    styles.add(ParagraphStyle(
        name='IssueTitle',
        parent=styles['Heading3'],
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceBefore=15,
        spaceAfter=5,
        textColor=colors.HexColor('#2d3748')
    ))

    styles.add(ParagraphStyle(
        name='IssueBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        leftIndent=15,
        textColor=colors.HexColor('#4a5568')
    ))

    styles.add(ParagraphStyle(
        name='Recommendation',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        leftIndent=15,
        textColor=colors.HexColor('#276749'),
        backColor=colors.HexColor('#f0fff4')
    ))

    styles.add(ParagraphStyle(
        name='CTATitle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2b6cb0'),
        spaceAfter=15
    ))

    styles.add(ParagraphStyle(
        name='CTABody',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='CTALink',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#3182ce'),
        fontName='Helvetica-Bold'
    ))

    return styles


def _build_cover_page(audit: AuditResult, styles, lang: str) -> list:
    """Build cover page with executive summary"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER

    content = []

    # Logo/Header area
    content.append(Spacer(1, 2*cm))
    content.append(Paragraph(rt("executive_summary", lang), styles['CoverTitle']))
    content.append(Spacer(1, 0.5*cm))

    # Site info
    content.append(Paragraph(f"<b>{rt('site_analyzed', lang)}:</b> {audit.url}", styles['CoverSubtitle']))
    content.append(Paragraph(
        f"<b>{rt('analysis_date', lang)}:</b> {audit.created_at.strftime('%d.%m.%Y %H:%M')}",
        styles['CoverSubtitle']
    ))

    content.append(Spacer(1, 1.5*cm))

    # Main score display
    score_color = _get_score_color(audit.overall_score)
    content.append(Paragraph(
        f"<font size='60' color='{score_color}'><b>{audit.overall_score}</b></font>"
        f"<font size='24' color='#718096'>/100</font>",
        ParagraphStyle('BigScore', alignment=TA_CENTER, spaceAfter=10)
    ))

    content.append(Paragraph(
        _get_score_label(audit.overall_score, lang),
        ParagraphStyle('ScoreLabel', alignment=TA_CENTER, fontSize=16,
                       textColor=colors.HexColor(score_color), spaceAfter=20)
    ))

    # Score interpretation
    content.append(Paragraph(
        f"<i>{_get_score_interpretation(audit.overall_score, lang)}</i>",
        ParagraphStyle('Interpretation', alignment=TA_CENTER, fontSize=11,
                       textColor=colors.HexColor('#4a5568'), spaceAfter=30)
    ))

    content.append(Spacer(1, 1*cm))

    # Category scores table
    scores_data = [
        [t("category", lang), t("score", lang), ""],
        ['Performance', f"{audit.performance_score or 'N/A'}/100", _get_score_bar(audit.performance_score)],
        ['SEO', f"{audit.seo_score or 'N/A'}/100", _get_score_bar(audit.seo_score)],
        ['Security', f"{audit.security_score or 'N/A'}/100", _get_score_bar(audit.security_score)],
        ['GDPR', f"{audit.gdpr_score or 'N/A'}/100", _get_score_bar(audit.gdpr_score)],
        ['Accessibility', f"{audit.accessibility_score or 'N/A'}/100", _get_score_bar(audit.accessibility_score)],
    ]

    scores_table = Table(scores_data, colWidths=[6*cm, 3*cm, 6*cm])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    content.append(scores_table)
    content.append(Spacer(1, 1*cm))

    # Issues summary
    severity_counts = {}
    for issue in audit.issues:
        sev = issue.severity.value
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    summary_text = (
        f"<b>{rt('total_issues', lang)}:</b> {len(audit.issues)} | "
        f"<font color='#e53e3e'><b>{t('critical', lang)}:</b> {severity_counts.get('critical', 0)}</font> | "
        f"<font color='#dd6b20'><b>{t('high', lang)}:</b> {severity_counts.get('high', 0)}</font> | "
        f"<font color='#d69e2e'><b>{t('medium', lang)}:</b> {severity_counts.get('medium', 0)}</font> | "
        f"<font color='#38a169'><b>{t('low', lang)}:</b> {severity_counts.get('low', 0)}</font>"
    )

    content.append(Paragraph(summary_text, ParagraphStyle(
        'Summary', alignment=TA_CENTER, fontSize=10, spaceAfter=20
    )))

    return content


def _build_category_analysis(audit: AuditResult, styles, lang: str) -> list:
    """Build category-by-category analysis with justifications"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
    from reportlab.lib.enums import TA_LEFT

    content = []

    content.append(Paragraph(rt("category_analysis", lang), styles['SectionTitle']))

    categories = [
        ("Performance", "performance", audit.performance_score, audit.performance, "perf_why"),
        ("SEO", "seo", audit.seo_score, audit.seo, "seo_why"),
        ("Security", "security", audit.security_score, audit.security, "sec_why"),
        ("GDPR", "gdpr", audit.gdpr_score, audit.gdpr, "gdpr_why"),
        ("Accessibility", "accessibility", audit.accessibility_score, audit.accessibility, "a11y_why"),
    ]

    for cat_name, cat_key, score, metrics, why_key in categories:
        if score is None:
            continue

        score_color = _get_score_color(score)
        cat_issues = [i for i in audit.issues if i.category.value == cat_key]

        # Category header with score
        cat_content = []

        header_data = [[
            Paragraph(f"<b>{cat_name}</b>", ParagraphStyle('CatName', fontSize=14, textColor=colors.HexColor('#1a365d'))),
            Paragraph(f"<font size='18' color='{score_color}'><b>{score}</b></font>/100",
                      ParagraphStyle('CatScore', alignment=TA_LEFT, fontSize=12))
        ]]

        header_table = Table(header_data, colWidths=[12*cm, 4*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf2f7')),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor(score_color)),
        ]))
        cat_content.append(header_table)
        cat_content.append(Spacer(1, 0.3*cm))

        # Why it matters
        cat_content.append(Paragraph(f"<b>{rt('why_matters', lang)}:</b>", styles['BodyText']))
        cat_content.append(Paragraph(rt(why_key, lang), styles['IssueBody']))
        cat_content.append(Spacer(1, 0.3*cm))

        # Score justification
        cat_content.append(Paragraph(f"<b>{rt('score_justification', lang)}:</b>", styles['BodyText']))
        justification = generate_score_justification(cat_key, score, metrics, cat_issues, lang)
        for line in justification.split('\n'):
            if line.strip():
                cat_content.append(Paragraph(line, styles['IssueBody']))

        cat_content.append(Spacer(1, 0.3*cm))

        # Key issues for this category
        if cat_issues:
            cat_content.append(Paragraph(f"<b>{rt('key_findings', lang)}:</b> {len(cat_issues)} " +
                                         ("probleme" if lang == "ro" else "issues"), styles['BodyText']))

            # Show top 3 issues for this category
            for issue in cat_issues[:3]:
                sev_color = _get_severity_color(issue.severity)
                cat_content.append(Paragraph(
                    f"<font color='{sev_color}'>•</font> {issue.title}",
                    styles['IssueBody']
                ))

        cat_content.append(Spacer(1, 0.5*cm))

        content.append(KeepTogether(cat_content))

    # Add screenshots if available
    content.append(Spacer(1, 1*cm))
    content.append(Paragraph(rt("screenshot_analysis", lang), styles['SubsectionTitle']))

    if audit.desktop_screenshot or audit.mobile_screenshot:
        screenshot_data = []
        if audit.desktop_screenshot:
            screenshot_data.append([
                Paragraph(f"<b>{rt('desktop_view', lang)}</b>", styles['BodyText']),
                Paragraph(f"<i>Screenshot disponibil</i>", styles['SmallText'])
            ])
        if audit.mobile_screenshot:
            screenshot_data.append([
                Paragraph(f"<b>{rt('mobile_view', lang)}</b>", styles['BodyText']),
                Paragraph(f"<i>Screenshot disponibil</i>", styles['SmallText'])
            ])

        if screenshot_data:
            ss_table = Table(screenshot_data, colWidths=[8*cm, 8*cm])
            ss_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            content.append(ss_table)
    else:
        content.append(Paragraph(
            "<i>" + ("Screenshot-urile nu sunt disponibile pentru acest audit." if lang == "ro"
                     else "Screenshots are not available for this audit.") + "</i>",
            styles['SmallText']
        ))

    return content


def _build_detailed_issues(audit: AuditResult, styles, lang: str) -> list:
    """Build detailed issues section with examples and time estimates"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
    from reportlab.lib.enums import TA_LEFT

    content = []

    content.append(Paragraph(rt("detailed_issues", lang), styles['SectionTitle']))
    content.append(Spacer(1, 0.5*cm))

    # Sort issues by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    sorted_issues = sorted(audit.issues, key=lambda x: severity_order.get(x.severity.value, 5))

    for i, issue in enumerate(sorted_issues[:25], 1):  # Limit to 25 issues
        sev_color = _get_severity_color(issue.severity)
        issue_content = []

        # Issue header
        issue_content.append(Paragraph(
            f"<font color='{sev_color}'><b>[{issue.severity.value.upper()}]</b></font> "
            f"<b>{rt('issue_number', lang)} #{i}:</b> {issue.title}",
            styles['IssueTitle']
        ))

        # Problem description
        issue_content.append(Paragraph(f"<b>{rt('problem', lang)}:</b>", styles['BodyText']))
        issue_content.append(Paragraph(issue.description, styles['IssueBody']))
        issue_content.append(Spacer(1, 0.2*cm))

        # Impact
        impact_text = _get_impact_text(issue.severity, lang)
        issue_content.append(Paragraph(f"<b>{rt('impact', lang)}:</b> {impact_text}", styles['IssueBody']))
        issue_content.append(Spacer(1, 0.2*cm))

        # Solution/Recommendation
        issue_content.append(Paragraph(f"<b>{rt('solution', lang)}:</b>", styles['BodyText']))
        issue_content.append(Paragraph(issue.recommendation, styles['Recommendation']))
        issue_content.append(Spacer(1, 0.2*cm))

        # Example if available
        if issue.affected_element:
            example_text = issue.affected_element[:200] + "..." if len(issue.affected_element) > 200 else issue.affected_element
            issue_content.append(Paragraph(
                f"<b>{rt('example', lang)}:</b> <font name='Courier' size='8'>{example_text}</font>",
                styles['IssueBody']
            ))
            issue_content.append(Spacer(1, 0.2*cm))

        # Time and difficulty
        difficulty = _get_difficulty_text(issue.complexity, lang)
        meta_data = [[
            Paragraph(f"<b>{rt('time_to_fix', lang)}:</b> {issue.estimated_hours}h", styles['SmallText']),
            Paragraph(f"<b>{rt('difficulty', lang)}:</b> {difficulty}", styles['SmallText'])
        ]]
        meta_table = Table(meta_data, colWidths=[8*cm, 8*cm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        issue_content.append(meta_table)

        issue_content.append(Spacer(1, 0.3*cm))
        issue_content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
        issue_content.append(Spacer(1, 0.3*cm))

        content.append(KeepTogether(issue_content))

    if len(audit.issues) > 25:
        content.append(Paragraph(
            f"<i>+ {len(audit.issues) - 25} " +
            ("alte probleme identificate" if lang == "ro" else "other issues identified") + "</i>",
            styles['SmallText']
        ))

    return content


def _build_action_plan(audit: AuditResult, styles, lang: str) -> list:
    """Build prioritized action plan"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem

    content = []

    content.append(Paragraph(rt("action_plan", lang), styles['SectionTitle']))
    content.append(Spacer(1, 0.5*cm))

    # Categorize issues by effort
    quick_wins = [i for i in audit.issues if i.estimated_hours <= 2 and i.severity in [Severity.CRITICAL, Severity.HIGH]]
    medium_effort = [i for i in audit.issues if 2 < i.estimated_hours <= 8]
    major_changes = [i for i in audit.issues if i.estimated_hours > 8]

    # Quick wins section
    content.append(Paragraph(f"<b>{rt('quick_wins', lang)}</b>", styles['SubsectionTitle']))
    content.append(Paragraph(rt('quick_wins_desc', lang), styles['BodyText']))
    content.append(Spacer(1, 0.3*cm))

    if quick_wins:
        for issue in quick_wins[:5]:
            content.append(Paragraph(
                f"• {issue.title} ({issue.estimated_hours}h)",
                styles['IssueBody']
            ))
    else:
        content.append(Paragraph(
            "<i>" + ("Nu exista castiguri rapide disponibile." if lang == "ro" else "No quick wins available.") + "</i>",
            styles['SmallText']
        ))

    content.append(Spacer(1, 0.5*cm))

    # Medium effort section
    content.append(Paragraph(f"<b>{rt('medium_effort', lang)}</b>", styles['SubsectionTitle']))
    if medium_effort:
        for issue in medium_effort[:5]:
            content.append(Paragraph(
                f"• {issue.title} ({issue.estimated_hours}h)",
                styles['IssueBody']
            ))
    else:
        content.append(Paragraph(
            "<i>" + ("Nu exista sarcini de efort mediu." if lang == "ro" else "No medium effort tasks.") + "</i>",
            styles['SmallText']
        ))

    content.append(Spacer(1, 0.5*cm))

    # Major changes section
    content.append(Paragraph(f"<b>{rt('major_changes', lang)}</b>", styles['SubsectionTitle']))
    if major_changes:
        for issue in major_changes[:5]:
            content.append(Paragraph(
                f"• {issue.title} ({issue.estimated_hours}h)",
                styles['IssueBody']
            ))
    else:
        content.append(Paragraph(
            "<i>" + ("Nu exista schimbari majore necesare." if lang == "ro" else "No major changes needed.") + "</i>",
            styles['SmallText']
        ))

    return content


def _build_summary_and_cta(audit: AuditResult, styles, lang: str) -> list:
    """Build summary and Website Guru CTA"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER

    content = []

    # Summary section
    content.append(Paragraph(rt("total_summary", lang), styles['SectionTitle']))
    content.append(Spacer(1, 0.5*cm))

    # Calculate totals
    total_hours = sum(i.estimated_hours for i in audit.issues)
    critical_count = len([i for i in audit.issues if i.severity == Severity.CRITICAL])
    estimated_cost = total_hours * 75  # €75/hour default rate

    summary_data = [
        [rt('total_issues', lang), str(len(audit.issues))],
        [rt('critical_issues', lang), str(critical_count)],
        [rt('total_time', lang), f"{total_hours:.0f} {rt('hours', lang)}"],
        [rt('estimated_cost', lang), f"€{estimated_cost:,.0f}"],
    ]

    summary_table = Table(summary_data, colWidths=[10*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f7fafc')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))

    content.append(summary_table)
    content.append(Spacer(1, 2*cm))

    # CTA Section
    content.append(Paragraph(rt("need_help", lang), styles['CTATitle']))
    content.append(Paragraph(rt("cta_title", lang), styles['CTABody']))
    content.append(Paragraph(rt("cta_desc", lang), styles['CTABody']))
    content.append(Spacer(1, 0.5*cm))

    # Benefits
    benefits = rt("cta_benefits", lang)
    for benefit in benefits:
        content.append(Paragraph(f"✓ {benefit}", ParagraphStyle(
            'Benefit', alignment=TA_CENTER, fontSize=11, textColor=colors.HexColor('#276749')
        )))

    content.append(Spacer(1, 1*cm))

    # CTA Link
    cta_box_data = [[
        Paragraph(
            f"<b>{rt('cta_link', lang)}</b><br/><br/>"
            f"<font size='16' color='#3182ce'><b>{rt('cta_url', lang)}</b></font>",
            ParagraphStyle('CTABox', alignment=TA_CENTER, fontSize=12)
        )
    ]]

    cta_table = Table(cta_box_data, colWidths=[16*cm])
    cta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ebf8ff')),
        ('PADDING', (0, 0), (-1, -1), 20),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#3182ce')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    content.append(cta_table)
    content.append(Spacer(1, 1*cm))

    # Footer
    content.append(Paragraph(
        f"{rt('report_footer', lang)} | {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        styles['SmallText']
    ))
    content.append(Paragraph(rt('confidential', lang), styles['SmallText']))

    return content


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def _get_score_color(score: Optional[int]) -> str:
    """Get color based on score"""
    if score is None:
        return '#718096'
    if score >= 80:
        return '#38a169'
    if score >= 60:
        return '#d69e2e'
    if score >= 40:
        return '#dd6b20'
    return '#e53e3e'


def _get_score_label(score: int, lang: str = "ro") -> str:
    """Get label based on score"""
    if score >= 90:
        return t("excellent", lang)
    if score >= 80:
        return t("very_good", lang)
    if score >= 70:
        return t("good", lang)
    if score >= 60:
        return t("satisfactory", lang)
    if score >= 40:
        return t("needs_improvement", lang)
    return t("significant_issues", lang)


def _get_score_interpretation(score: int, lang: str = "ro") -> str:
    """Get detailed score interpretation"""
    if score >= 90:
        return rt("score_90_100", lang)
    if score >= 80:
        return rt("score_80_89", lang)
    if score >= 70:
        return rt("score_70_79", lang)
    if score >= 60:
        return rt("score_60_69", lang)
    if score >= 40:
        return rt("score_40_59", lang)
    return rt("score_0_39", lang)


def _get_score_bar(score: Optional[int]) -> str:
    """Generate text-based score bar"""
    if score is None:
        return "N/A"

    filled = int(score / 10)
    empty = 10 - filled

    color = _get_score_color(score)
    bar = "█" * filled + "░" * empty

    return f"<font color='{color}'>{bar}</font>"


def _get_severity_color(severity: Severity) -> str:
    """Get color for severity level"""
    severity_colors = {
        Severity.CRITICAL: '#e53e3e',
        Severity.HIGH: '#dd6b20',
        Severity.MEDIUM: '#d69e2e',
        Severity.LOW: '#38a169',
        Severity.INFO: '#3182ce'
    }
    return severity_colors.get(severity, '#718096')


def _get_impact_text(severity: Severity, lang: str) -> str:
    """Get impact text based on severity"""
    impacts = {
        Severity.CRITICAL: "impact_critical",
        Severity.HIGH: "impact_high",
        Severity.MEDIUM: "impact_medium",
        Severity.LOW: "impact_low",
        Severity.INFO: "impact_low"
    }
    return rt(impacts.get(severity, "impact_medium"), lang)


def _get_difficulty_text(complexity: str, lang: str) -> str:
    """Get difficulty text based on complexity"""
    difficulties = {
        "simple": "diff_simple",
        "medium": "diff_medium",
        "complex": "diff_complex"
    }
    return rt(difficulties.get(complexity, "diff_medium"), lang)


# ============================================================================
# FALLBACK SIMPLE REPORT
# ============================================================================
async def _generate_simple_report(audit: AuditResult, lang: str = "ro") -> str:
    """Generate a simple text report when ReportLab is not available"""

    output_dir = Path(__file__).parent.parent / 'data' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"audit_report_{audit.id[:8]}_{datetime.now().strftime('%Y%m%d')}.txt"
    filepath = output_dir / filename

    content = f"""
================================================================================
                         {rt("executive_summary", lang)}
================================================================================

{rt("site_analyzed", lang)}: {audit.url}
{rt("analysis_date", lang)}: {audit.created_at.strftime('%d.%m.%Y')}

{rt("your_score", lang)}: {audit.overall_score}/100

--------------------------------------------------------------------------------
{rt("category_analysis", lang).upper()}
--------------------------------------------------------------------------------
Performance:    {audit.performance_score or 'N/A'}/100
SEO:            {audit.seo_score or 'N/A'}/100
Security:       {audit.security_score or 'N/A'}/100
GDPR:           {audit.gdpr_score or 'N/A'}/100
Accessibility:  {audit.accessibility_score or 'N/A'}/100

--------------------------------------------------------------------------------
{rt("detailed_issues", lang).upper()} ({len(audit.issues)} total)
--------------------------------------------------------------------------------
"""

    for i, issue in enumerate(audit.issues, 1):
        content += f"""
{i}. [{issue.severity.value.upper()}] {issue.title}
   {rt("problem", lang)}: {issue.description}
   {rt("solution", lang)}: {issue.recommendation}
   {rt("time_to_fix", lang)}: {issue.estimated_hours}h | {rt("difficulty", lang)}: {issue.complexity}
"""

    content += f"""
--------------------------------------------------------------------------------
{rt("need_help", lang)}
--------------------------------------------------------------------------------
{rt("cta_title", lang)}
{rt("cta_desc", lang)}

{rt("cta_link", lang)}
{rt("cta_url", lang)}

--------------------------------------------------------------------------------
                    {rt("report_footer", lang)}
================================================================================
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(filepath)
