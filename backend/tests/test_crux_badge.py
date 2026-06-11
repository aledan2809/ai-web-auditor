"""
Tests — CrUX field data (services/crux.py) + embeddable badge (services/badge.py).
Secondary roadmap items (test-tooling 2026-06-11). IO-free except the mocked
fetch test; the real network path is flag-gated on CRUX_API_KEY.
"""

import asyncio

from services.crux import (
    parse_crux_record, rate_metric, crux_issues, fetch_crux_metrics, CRUX_THRESHOLDS,
)
from services.badge import build_badge_svg, score_color
from models.schemas import Severity


def _record(lcp=None, inp=None, cls=None):
    metrics = {}
    if lcp is not None:
        metrics["largest_contentful_paint"] = {"percentiles": {"p75": lcp}}
    if inp is not None:
        metrics["interaction_to_next_paint"] = {"percentiles": {"p75": inp}}
    if cls is not None:
        metrics["cumulative_layout_shift"] = {"percentiles": {"p75": cls}}
    return {"record": {"metrics": metrics}}


class TestParseCrux:
    def test_parses_all_three_p75(self):
        parsed = parse_crux_record(_record(lcp=2300, inp=180, cls="0.05"))
        assert parsed == {
            "largest_contentful_paint": 2300.0,
            "interaction_to_next_paint": 180.0,
            "cumulative_layout_shift": 0.05,
        }

    def test_partial_record_keeps_present_metrics(self):
        parsed = parse_crux_record(_record(lcp=5000))
        assert list(parsed) == ["largest_contentful_paint"]

    def test_empty_or_malformed_returns_none(self):
        assert parse_crux_record({}) is None
        assert parse_crux_record(None) is None
        assert parse_crux_record({"record": {"metrics": {}}}) is None
        assert parse_crux_record(_record(lcp="not-a-number")) is None


class TestRating:
    def test_thresholds(self):
        assert rate_metric("largest_contentful_paint", 2500) == "good"
        assert rate_metric("largest_contentful_paint", 3000) == "needs-improvement"
        assert rate_metric("largest_contentful_paint", 4001) == "poor"
        assert rate_metric("cumulative_layout_shift", 0.09) == "good"
        assert rate_metric("interaction_to_next_paint", 600) == "poor"


class TestCruxIssues:
    def test_good_metrics_produce_no_issues(self):
        parsed = {"largest_contentful_paint": 2000.0, "cumulative_layout_shift": 0.05}
        assert crux_issues(parsed, "https://x.com") == []

    def test_poor_is_high_needs_improvement_is_medium(self):
        parsed = {"largest_contentful_paint": 4500.0, "interaction_to_next_paint": 300.0}
        issues = crux_issues(parsed, "https://x.com", lang="en")
        by_sev = {i.severity for i in issues}
        assert by_sev == {Severity.HIGH, Severity.MEDIUM}
        lcp = next(i for i in issues if "LCP" in i.title)
        assert "4.50s" in lcp.title
        assert lcp.category.value == "performance"

    def test_ro_and_en_localization(self):
        parsed = {"cumulative_layout_shift": 0.4}
        ro = crux_issues(parsed, "https://x.com", lang="ro")[0]
        en = crux_issues(parsed, "https://x.com", lang="en")[0]
        assert "utilizatori reali" in ro.title
        assert "Real-user" in en.title

    def test_none_parsed_is_safe(self):
        assert crux_issues(None, "https://x.com") == []


class TestFetchCrux:
    def test_no_api_key_returns_none_without_network(self, monkeypatch):
        monkeypatch.delenv("CRUX_API_KEY", raising=False)
        assert asyncio.run(fetch_crux_metrics("https://x.com")) is None

    def test_mocked_client_parses_response(self):
        class FakeResp:
            status_code = 200
            def json(self):
                return _record(lcp=3100)
        class FakeClient:
            async def post(self, url, json=None):
                assert "key=K" in url and json["url"] == "https://x.com"
                return FakeResp()
            async def aclose(self):  # pragma: no cover — not own_client
                raise AssertionError("injected client must not be closed")
        parsed = asyncio.run(fetch_crux_metrics("https://x.com", api_key="K", client=FakeClient()))
        assert parsed == {"largest_contentful_paint": 3100.0}

    def test_non_200_and_exception_return_none(self):
        class Fake404:
            async def post(self, *a, **k):
                class R: status_code = 404
                return R()
            async def aclose(self): pass
        class FakeBoom:
            async def post(self, *a, **k):
                raise RuntimeError("net down")
            async def aclose(self): pass
        assert asyncio.run(fetch_crux_metrics("https://x.com", api_key="K", client=Fake404())) is None
        assert asyncio.run(fetch_crux_metrics("https://x.com", api_key="K", client=FakeBoom())) is None


class TestBadge:
    def test_svg_contains_score_and_label(self):
        svg = build_badge_svg(87)
        assert svg.startswith("<svg") and "87/100" in svg and "TechBiz Audit" in svg

    def test_color_bands(self):
        assert score_color(85) == "#22c55e"
        assert score_color(65) == "#f59e0b"
        assert score_color(30) == "#ef4444"
        assert score_color(85) in build_badge_svg(85)
        assert score_color(10) in build_badge_svg(10)

    def test_score_clamped(self):
        assert "100/100" in build_badge_svg(250)
        assert "0/100" in build_badge_svg(-5)
