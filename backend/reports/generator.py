"""
PDF Report Generator - Creates professional audit reports
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import io

from models.schemas import AuditResult, Severity


async def generate_pdf_report(audit: AuditResult) -> str:
    """Generate a PDF report from audit results"""

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        return await _generate_simple_report(audit)

    # Create output directory
    output_dir = Path(__file__).parent.parent / 'data' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"audit_report_{audit.id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
    filepath = output_dir / filename

    # Create PDF
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title2',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#1a365d')
    ))

    # Build content
    content = []

    # Title page
    content.append(Spacer(1, 3*cm))
    content.append(Paragraph("RAPORT DE AUDIT WEB", styles['Title2']))
    content.append(Paragraph(f"{audit.url}", styles['Subtitle']))
    content.append(Spacer(1, 1*cm))
    content.append(Paragraph(
        f"Data auditului: {audit.created_at.strftime('%d %B %Y')}",
        styles['Subtitle']
    ))
    content.append(Spacer(1, 2*cm))

    # Overall score
    score_color = _get_score_color(audit.overall_score)
    content.append(Paragraph(
        f"<font size='48' color='{score_color}'>{audit.overall_score}</font><font size='24'>/100</font>",
        ParagraphStyle('Score', alignment=TA_CENTER, spaceAfter=30)
    ))
    content.append(Paragraph(
        _get_score_label(audit.overall_score),
        ParagraphStyle('ScoreLabel', alignment=TA_CENTER, fontSize=14, textColor=colors.HexColor(score_color))
    ))

    content.append(PageBreak())

    # Scores summary
    content.append(Paragraph("Scor pe Categorii", styles['SectionHeader']))

    scores_data = [
        ['Categorie', 'Scor', 'Status'],
        ['Performance', str(audit.performance_score or 'N/A'), _get_status_icon(audit.performance_score)],
        ['SEO', str(audit.seo_score or 'N/A'), _get_status_icon(audit.seo_score)],
        ['Security', str(audit.security_score or 'N/A'), _get_status_icon(audit.security_score)],
        ['GDPR', str(audit.gdpr_score or 'N/A'), _get_status_icon(audit.gdpr_score)],
        ['Accessibility', str(audit.accessibility_score or 'N/A'), _get_status_icon(audit.accessibility_score)],
    ]

    scores_table = Table(scores_data, colWidths=[8*cm, 3*cm, 4*cm])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    content.append(scores_table)
    content.append(Spacer(1, 1*cm))

    # Issues summary
    content.append(Paragraph("Probleme Identificate", styles['SectionHeader']))

    # Count by severity
    severity_counts = {}
    for issue in audit.issues:
        sev = issue.severity.value
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    issues_summary = [
        ['Severitate', 'Număr'],
        ['Critice', str(severity_counts.get('critical', 0))],
        ['Importante', str(severity_counts.get('high', 0))],
        ['Medii', str(severity_counts.get('medium', 0))],
        ['Minore', str(severity_counts.get('low', 0))],
    ]

    issues_table = Table(issues_summary, colWidths=[8*cm, 4*cm])
    issues_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fed7d7')),  # Critical - red
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#feebc8')),  # High - orange
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#fefcbf')),  # Medium - yellow
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#c6f6d5')),  # Low - green
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))

    content.append(issues_table)
    content.append(PageBreak())

    # Detailed issues
    content.append(Paragraph("Detalii Probleme", styles['SectionHeader']))

    for i, issue in enumerate(audit.issues[:30], 1):  # Limit to 30 issues
        severity_color = _get_severity_color(issue.severity)

        content.append(Paragraph(
            f"<font color='{severity_color}'>[{issue.severity.value.upper()}]</font> {issue.title}",
            ParagraphStyle('IssueTitle', fontSize=11, fontName='Helvetica-Bold', spaceBefore=10)
        ))
        content.append(Paragraph(
            issue.description,
            ParagraphStyle('IssueDesc', fontSize=10, textColor=colors.grey, leftIndent=20)
        ))
        content.append(Paragraph(
            f"<b>Recomandare:</b> {issue.recommendation}",
            ParagraphStyle('IssueRec', fontSize=10, leftIndent=20, spaceBefore=5)
        ))
        content.append(Paragraph(
            f"Timp estimat: {issue.estimated_hours}h | Complexitate: {issue.complexity}",
            ParagraphStyle('IssueMeta', fontSize=9, textColor=colors.grey, leftIndent=20, spaceAfter=10)
        ))

    # Footer
    content.append(Spacer(1, 2*cm))
    content.append(Paragraph(
        "Raport generat de AI Web Auditor",
        ParagraphStyle('Footer', fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    ))
    content.append(Paragraph(
        datetime.now().strftime('%d.%m.%Y %H:%M'),
        ParagraphStyle('FooterDate', fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    ))

    # Build PDF
    doc.build(content)

    return str(filepath)


async def _generate_simple_report(audit: AuditResult) -> str:
    """Generate a simple text report when ReportLab is not available"""

    output_dir = Path(__file__).parent.parent / 'data' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"audit_report_{audit.id[:8]}_{datetime.now().strftime('%Y%m%d')}.txt"
    filepath = output_dir / filename

    content = f"""
================================================================================
                         RAPORT DE AUDIT WEB
================================================================================

URL: {audit.url}
Data: {audit.created_at.strftime('%d %B %Y')}

SCOR GENERAL: {audit.overall_score}/100

--------------------------------------------------------------------------------
SCORURI PE CATEGORII
--------------------------------------------------------------------------------
Performance:    {audit.performance_score or 'N/A'}/100
SEO:            {audit.seo_score or 'N/A'}/100
Security:       {audit.security_score or 'N/A'}/100
GDPR:           {audit.gdpr_score or 'N/A'}/100
Accessibility:  {audit.accessibility_score or 'N/A'}/100

--------------------------------------------------------------------------------
PROBLEME IDENTIFICATE ({len(audit.issues)} total)
--------------------------------------------------------------------------------
"""

    for i, issue in enumerate(audit.issues, 1):
        content += f"""
{i}. [{issue.severity.value.upper()}] {issue.title}
   Categorie: {issue.category.value}
   {issue.description}
   Recomandare: {issue.recommendation}
   Timp estimat: {issue.estimated_hours}h
"""

    content += """
--------------------------------------------------------------------------------
                    Generat de AI Web Auditor
================================================================================
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(filepath)


def _get_score_color(score: Optional[int]) -> str:
    """Get color based on score"""
    if score is None:
        return '#718096'
    if score >= 80:
        return '#38a169'  # Green
    if score >= 60:
        return '#d69e2e'  # Yellow
    if score >= 40:
        return '#dd6b20'  # Orange
    return '#e53e3e'  # Red


def _get_score_label(score: int) -> str:
    """Get label based on score"""
    if score >= 90:
        return "Excelent"
    if score >= 80:
        return "Foarte Bun"
    if score >= 70:
        return "Bun"
    if score >= 60:
        return "Satisfăcător"
    if score >= 40:
        return "Necesită Îmbunătățiri"
    return "Probleme Semnificative"


def _get_status_icon(score: Optional[int]) -> str:
    """Get status text based on score"""
    if score is None:
        return "N/A"
    if score >= 80:
        return "✓ Bun"
    if score >= 60:
        return "~ Satisfăcător"
    return "✗ Necesită atenție"


def _get_severity_color(severity: Severity) -> str:
    """Get color for severity level"""
    colors = {
        Severity.CRITICAL: '#e53e3e',
        Severity.HIGH: '#dd6b20',
        Severity.MEDIUM: '#d69e2e',
        Severity.LOW: '#38a169',
        Severity.INFO: '#3182ce'
    }
    return colors.get(severity, '#718096')
