"""
AIWebAuditor CLI - Standalone audit/fix/retest commands
"""

import asyncio
import json
import os
import sys
from datetime import date, datetime
from typing import List, Optional

import typer

from .core.auditor import run_audit
from .core.config import load_config, get_enabled_categories
from .core.fixer import apply_fixes, generate_fixes
from .core.logger import setup_logger
from .core.plugin_loader import load_plugins, run_plugin_rules
from .core.retester import run_retest
from .schemas.models import AuditReport

app = typer.Typer(
    name="aiwebauditor",
    help="AIWebAuditor - Standalone Web Audit CLI (AUDIT + FIX + RETEST)",
    add_completion=False,
)


def _default_output_dir() -> str:
    today = date.today().isoformat()
    return os.path.join("reports", f"audit-{today}", "aiwebauditor")


def _validate_url(url: str) -> str:
    """Basic URL validation to prevent SSRF."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        typer.echo(f"Error: Only http/https URLs are allowed, got '{parsed.scheme}'", err=True)
        raise typer.Exit(1)
    if not parsed.netloc:
        typer.echo("Error: Invalid URL - no host specified", err=True)
        raise typer.Exit(1)
    # Block private IPs
    host = parsed.hostname or ""
    if host in ("localhost", "127.0.0.1", "0.0.0.0") or host.startswith("192.168.") or host.startswith("10."):
        typer.echo("Error: Private/local URLs are not allowed", err=True)
        raise typer.Exit(1)
    return url


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


@app.command()
def audit(
    url: str = typer.Argument(..., help="URL to audit"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    categories: Optional[str] = typer.Option(None, "--categories", "-c", help="Comma-separated categories (seo,accessibility,security,performance)"),
    config_file: Optional[str] = typer.Option(None, "--config", help="Path to config.json"),
    plugins_dir: Optional[str] = typer.Option(None, "--plugins", "-p", help="Path to plugins directory"),
):
    """Run a web audit on the specified URL."""
    url = _validate_url(url)

    if output_dir is None:
        output_dir = _default_output_dir()
    _ensure_dir(output_dir)

    config = load_config(config_file)
    logger = setup_logger(output_dir)

    # Determine categories
    if categories:
        cats = [c.strip() for c in categories.split(",")]
    else:
        cats = get_enabled_categories(config)

    typer.echo(f"AIWebAuditor v1.0 - Auditing {url}")
    typer.echo(f"Categories: {', '.join(cats)}")
    typer.echo(f"Output: {output_dir}")
    typer.echo("")

    # Run audit
    report = asyncio.run(run_audit(url, cats))

    # Run plugin rules
    p_dir = plugins_dir or config.get("plugins_dir", "plugins")
    if os.path.isdir(p_dir):
        plugin_rules = load_plugins(p_dir)
        if plugin_rules:
            import httpx
            try:
                resp = httpx.get(url, follow_redirects=True, timeout=30.0)
                plugin_issues = run_plugin_rules(plugin_rules, resp.text, url)
                report.issues.extend(plugin_issues)
                report.total_issues = len(report.issues)
                for pi in plugin_issues:
                    sev = pi.severity.value
                    report.issues_by_severity[sev] = report.issues_by_severity.get(sev, 0) + 1
            except Exception as e:
                logger.error(f"Plugin execution failed: {e}")

    # Save report
    report_path = os.path.join(output_dir, "audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, default=str)

    # Print summary
    typer.echo("=" * 60)
    typer.echo(f"AUDIT COMPLETE")
    typer.echo(f"Overall Score: {report.overall_score}/100")
    typer.echo(f"Total Issues: {report.total_issues}")
    if report.issues_by_severity:
        typer.echo(f"By Severity: {json.dumps(report.issues_by_severity)}")
    typer.echo("")
    for cs in report.category_scores:
        typer.echo(f"  {cs.category.value.upper():15s} Score: {cs.score:3d}/100  Issues: {cs.issues_count}")
    typer.echo("")
    typer.echo(f"Report saved: {report_path}")
    typer.echo("=" * 60)

    logger.info(f"Audit report saved to {report_path}")


@app.command()
def fix(
    input_file: str = typer.Argument(..., help="Path to audit_report.json"),
    auto_apply: bool = typer.Option(False, "--auto-apply", help="Auto-apply fixes to local HTML files"),
    html_file: Optional[str] = typer.Option(None, "--html", help="Path to local HTML file to fix"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Output directory for patches"),
):
    """Generate fix patches for audit issues."""
    if not os.path.exists(input_file):
        typer.echo(f"Error: File not found: {input_file}", err=True)
        raise typer.Exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    report = AuditReport(**data)

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(input_file), "fixes")
    _ensure_dir(output_dir)

    logger = setup_logger(output_dir)

    typer.echo(f"AIWebAuditor Fix - Processing {report.total_issues} issues")

    # Get HTML content
    html_content = None
    if html_file and os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        # Fetch from URL
        import httpx
        try:
            typer.echo(f"Fetching HTML from {report.url}...")
            resp = httpx.get(report.url, follow_redirects=True, timeout=30.0)
            html_content = resp.text
        except Exception as e:
            typer.echo(f"Warning: Could not fetch URL: {e}", err=True)

    # Generate fixes
    fix_report = generate_fixes(report, html_content)

    # Save fix report
    fix_path = os.path.join(os.path.dirname(output_dir), "fix_report.json")
    with open(fix_path, "w", encoding="utf-8") as f:
        json.dump(fix_report.model_dump(), f, indent=2, default=str)

    # Save individual diffs
    for i, patch in enumerate(fix_report.patches):
        diff_file = os.path.join(output_dir, f"patch_{i+1}_{patch.issue_id[:30]}.diff")
        with open(diff_file, "w", encoding="utf-8") as f:
            f.write(f"# Fix: {patch.description}\n")
            f.write(f"# Issue: {patch.issue_id}\n\n")
            f.write(patch.diff)

    # Auto-apply
    if auto_apply and html_content and html_file:
        # Backup
        backup_path = html_file + ".bak"
        import shutil
        shutil.copy2(html_file, backup_path)
        typer.echo(f"Backup created: {backup_path}")

        fixed_html = apply_fixes(html_content, fix_report)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(fixed_html)
        typer.echo(f"Fixes applied to: {html_file}")

    # Summary
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("FIX REPORT")
    typer.echo(f"Total issues: {fix_report.total_issues}")
    typer.echo(f"Fixable: {fix_report.fixable_issues}")
    typer.echo(f"Patches generated: {fix_report.patches_generated}")
    typer.echo(f"Unfixable: {len(fix_report.unfixable_reasons)}")
    typer.echo("")
    for patch in fix_report.patches:
        typer.echo(f"  [PATCH] {patch.description}")
    typer.echo("")
    if fix_report.unfixable_reasons:
        typer.echo("Unfixable issues (manual fix required):")
        for iid, reason in list(fix_report.unfixable_reasons.items())[:10]:
            typer.echo(f"  - {reason}")
    typer.echo("")
    typer.echo(f"Fix report: {fix_path}")
    typer.echo(f"Patches dir: {output_dir}")
    typer.echo("=" * 60)


@app.command()
def retest(
    input_file: str = typer.Argument(..., help="Path to original audit_report.json"),
    url: Optional[str] = typer.Option(None, "--url", help="URL to retest (defaults to original)"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
):
    """Re-audit and compare with the original audit results."""
    if not os.path.exists(input_file):
        typer.echo(f"Error: File not found: {input_file}", err=True)
        raise typer.Exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    original = AuditReport(**data)

    retest_url = url or original.url
    retest_url = _validate_url(retest_url)

    if output_dir is None:
        output_dir = os.path.dirname(input_file)
    _ensure_dir(output_dir)

    logger = setup_logger(output_dir)

    typer.echo(f"AIWebAuditor Retest - Re-auditing {retest_url}")
    typer.echo(f"Comparing with original ({original.total_issues} issues, score {original.overall_score})")
    typer.echo("")

    retest_report = asyncio.run(run_retest(retest_url, original))

    # Save report
    retest_path = os.path.join(output_dir, "retest_report.json")
    with open(retest_path, "w", encoding="utf-8") as f:
        json.dump(retest_report.model_dump(), f, indent=2, default=str)

    # Summary
    typer.echo("=" * 60)
    typer.echo("RETEST REPORT")
    typer.echo(f"Score: {retest_report.original_score} -> {retest_report.retest_score} ({retest_report.score_change:+d})")
    typer.echo(f"Resolved: {retest_report.resolved_issues}/{retest_report.total_original_issues} ({retest_report.resolved_percentage}%)")
    typer.echo(f"Remaining: {retest_report.remaining_issues}")
    typer.echo(f"New issues: {retest_report.new_issues}")
    typer.echo("")

    # Show resolved
    resolved = [c for c in retest_report.comparisons if c.status.value == "fixed"]
    if resolved:
        typer.echo("Resolved issues:")
        for c in resolved:
            typer.echo(f"  [FIXED] {c.title}")

    # Show remaining
    remaining = [c for c in retest_report.comparisons if c.status.value == "not_fixed"]
    if remaining:
        typer.echo("Remaining issues:")
        for c in remaining[:10]:
            typer.echo(f"  [OPEN]  {c.title}")

    typer.echo("")
    typer.echo(f"Report saved: {retest_path}")
    typer.echo("=" * 60)


@app.command()
def version():
    """Show version information."""
    typer.echo("AIWebAuditor v1.0.0 - Standalone Web Audit CLI")
    typer.echo("Engine: AUDIT + FIX + RETEST")
    typer.echo("Categories: SEO, Accessibility, Security, Performance")


def main():
    app()
