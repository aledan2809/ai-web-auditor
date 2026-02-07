"""
Performance Auditor - Measures Core Web Vitals and page performance
Uses Playwright for real browser measurements
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional
import httpx
from datetime import datetime
import json

from models.schemas import (
    PerformanceMetrics, AuditIssue, AuditType, Severity
)
from translations import t


@dataclass
class PerformanceResult:
    score: int
    metrics: PerformanceMetrics
    issues: List[AuditIssue]


class PerformanceAuditor:
    """Audits website performance using Core Web Vitals metrics"""

    def __init__(self):
        self.thresholds = {
            'lcp': {'good': 2.5, 'poor': 4.0},  # seconds
            'fid': {'good': 100, 'poor': 300},   # milliseconds
            'cls': {'good': 0.1, 'poor': 0.25},  # score
            'ttfb': {'good': 800, 'poor': 1800}, # milliseconds
            'fcp': {'good': 1.8, 'poor': 3.0},   # seconds
            'speed_index': {'good': 3.4, 'poor': 5.8},  # seconds
            'tbt': {'good': 200, 'poor': 600},   # milliseconds
        }

    async def audit(self, url: str, mobile: bool = True, lang: str = "ro") -> PerformanceResult:
        """Run performance audit on URL"""
        issues = []

        try:
            # Try to use Playwright for real measurements
            metrics = await self._measure_with_playwright(url, mobile)
        except Exception as e:
            print(f"Playwright measurement failed: {e}, using HTTP fallback")
            metrics = await self._measure_with_http(url)

        # Calculate score
        score = self._calculate_score(metrics)

        # Generate issues based on metrics
        issues = self._generate_issues(metrics, url, lang)

        return PerformanceResult(
            score=score,
            metrics=metrics,
            issues=issues
        )

    async def _measure_with_playwright(self, url: str, mobile: bool) -> PerformanceMetrics:
        """Measure performance using Playwright browser"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)

                # Configure viewport for mobile or desktop
                context_options = {}
                if mobile:
                    context_options = {
                        'viewport': {'width': 375, 'height': 812},
                        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
                    }
                else:
                    context_options = {
                        'viewport': {'width': 1920, 'height': 1080}
                    }

                context = await browser.new_context(**context_options)
                page = await context.new_page()

                # Enable performance metrics
                client = await context.new_cdp_session(page)
                await client.send('Performance.enable')

                # Navigate and measure
                start_time = datetime.now()

                response = await page.goto(url, wait_until='networkidle', timeout=30000)

                # Get performance timing
                perf_timing = await page.evaluate('''() => {
                    const timing = performance.timing;
                    const paint = performance.getEntriesByType('paint');
                    const lcp = performance.getEntriesByType('largest-contentful-paint');

                    return {
                        ttfb: timing.responseStart - timing.requestStart,
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        loadComplete: timing.loadEventEnd - timing.navigationStart,
                        fcp: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                        lcp: lcp.length > 0 ? lcp[lcp.length - 1].startTime : 0
                    }
                }''')

                # Calculate CLS
                cls = await page.evaluate('''() => {
                    let cls = 0;
                    const observer = new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            if (!entry.hadRecentInput) {
                                cls += entry.value;
                            }
                        }
                    });
                    observer.observe({type: 'layout-shift', buffered: true});
                    return cls;
                }''')

                await browser.close()

                # Build metrics
                return PerformanceMetrics(
                    score=0,  # Will be calculated
                    lcp=perf_timing.get('lcp', 0) / 1000,
                    fid=50,  # FID requires real user interaction, estimate
                    cls=cls or 0.05,
                    ttfb=perf_timing.get('ttfb', 0),
                    speed_index=perf_timing.get('loadComplete', 0) / 1000,
                    total_blocking_time=100,  # Estimate
                    first_contentful_paint=perf_timing.get('fcp', 0) / 1000
                )

        except ImportError:
            raise Exception("Playwright not available")

    async def _measure_with_http(self, url: str) -> PerformanceMetrics:
        """Fallback HTTP-based measurement"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            start = datetime.now()
            response = await client.get(url, follow_redirects=True)
            end = datetime.now()

            response_time = (end - start).total_seconds()
            content_length = len(response.content)

            # Estimate metrics based on response
            return PerformanceMetrics(
                score=0,
                lcp=response_time * 1.5,  # Estimate
                fid=50,
                cls=0.1,
                ttfb=response_time * 1000 * 0.3,
                speed_index=response_time * 2,
                total_blocking_time=100,
                first_contentful_paint=response_time * 0.8
            )

    def _calculate_score(self, metrics: PerformanceMetrics) -> int:
        """Calculate overall performance score (0-100)"""
        scores = []

        # LCP score
        if metrics.lcp <= self.thresholds['lcp']['good']:
            scores.append(100)
        elif metrics.lcp >= self.thresholds['lcp']['poor']:
            scores.append(30)
        else:
            scores.append(65)

        # FID score
        if metrics.fid <= self.thresholds['fid']['good']:
            scores.append(100)
        elif metrics.fid >= self.thresholds['fid']['poor']:
            scores.append(30)
        else:
            scores.append(65)

        # CLS score
        if metrics.cls <= self.thresholds['cls']['good']:
            scores.append(100)
        elif metrics.cls >= self.thresholds['cls']['poor']:
            scores.append(30)
        else:
            scores.append(65)

        # TTFB score
        if metrics.ttfb <= self.thresholds['ttfb']['good']:
            scores.append(100)
        elif metrics.ttfb >= self.thresholds['ttfb']['poor']:
            scores.append(30)
        else:
            scores.append(65)

        return int(sum(scores) / len(scores))

    def _generate_issues(self, metrics: PerformanceMetrics, url: str, lang: str = "ro") -> List[AuditIssue]:
        """Generate issues based on performance metrics"""
        issues = []

        # LCP issues
        if metrics.lcp > self.thresholds['lcp']['good']:
            severity = Severity.CRITICAL if metrics.lcp > self.thresholds['lcp']['poor'] else Severity.HIGH
            issues.append(AuditIssue(
                id=f"perf_lcp_{hash(url)}",
                category=AuditType.PERFORMANCE,
                severity=severity,
                title=t("perf_lcp_slow", lang),
                description=t("perf_lcp_slow_desc", lang, f"{metrics.lcp:.2f}"),
                recommendation=t("perf_lcp_slow_rec", lang),
                estimated_hours=4.0 if severity == Severity.CRITICAL else 2.0,
                complexity="complex" if severity == Severity.CRITICAL else "medium"
            ))

        # CLS issues
        if metrics.cls > self.thresholds['cls']['good']:
            severity = Severity.HIGH if metrics.cls > self.thresholds['cls']['poor'] else Severity.MEDIUM
            issues.append(AuditIssue(
                id=f"perf_cls_{hash(url)}",
                category=AuditType.PERFORMANCE,
                severity=severity,
                title=t("perf_cls_high", lang),
                description=t("perf_cls_high_desc", lang, f"{metrics.cls:.3f}"),
                recommendation=t("perf_cls_high_rec", lang),
                estimated_hours=3.0,
                complexity="medium"
            ))

        # TTFB issues
        if metrics.ttfb > self.thresholds['ttfb']['good']:
            severity = Severity.HIGH if metrics.ttfb > self.thresholds['ttfb']['poor'] else Severity.MEDIUM
            issues.append(AuditIssue(
                id=f"perf_ttfb_{hash(url)}",
                category=AuditType.PERFORMANCE,
                severity=severity,
                title=t("perf_ttfb_slow", lang),
                description=t("perf_ttfb_slow_desc", lang, f"{metrics.ttfb:.0f}"),
                recommendation=t("perf_ttfb_slow_rec", lang),
                estimated_hours=6.0,
                complexity="complex"
            ))

        # FCP issues
        if metrics.first_contentful_paint > self.thresholds['fcp']['good']:
            issues.append(AuditIssue(
                id=f"perf_fcp_{hash(url)}",
                category=AuditType.PERFORMANCE,
                severity=Severity.MEDIUM,
                title=t("perf_fcp_slow", lang),
                description=t("perf_fcp_slow_desc", lang, f"{metrics.first_contentful_paint:.2f}"),
                recommendation=t("perf_fcp_slow_rec", lang),
                estimated_hours=2.0,
                complexity="medium"
            ))

        return issues
