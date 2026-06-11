"""Tests — concurrent auditor execution + preserved error policy (roadmap R5)."""
import asyncio
import time

from services.audit_runner import select_auditors, gather_auditor_results


class FakeResult:
    def __init__(self, score):
        self.score = score


def fake_specs(delay=0.05, fail=None):
    """Build specs whose factories sleep `delay` then return FakeResult(name-hash)."""
    fail = fail or set()

    def make(name):
        async def factory(url, mobile, lang):
            await asyncio.sleep(delay)
            if name in fail:
                raise RuntimeError(f"{name} boom")
            return FakeResult(len(name))
        return factory

    return [
        ("performance", "core", "performance", make("performance")),
        ("seo", "core", "seo", make("seo")),
        ("security", "core", "security", make("security")),
        ("gdpr", "core", "gdpr", make("gdpr")),
        ("accessibility", "core", "accessibility", make("accessibility")),
        ("mobile_ux", "extra", None, make("mobile_ux")),
        ("trust", "extra", None, make("trust")),
        ("competitor", "extra", None, make("competitor")),
    ]


class TestSelection:
    def test_full_selects_everything(self):
        sel = select_auditors(["full"], fake_specs())
        assert {s[0] for s in sel} == {
            "performance", "seo", "security", "gdpr", "accessibility",
            "mobile_ux", "trust", "competitor",
        }

    def test_named_core_only_no_extras(self):
        sel = select_auditors(["seo", "security"], fake_specs())
        assert {s[0] for s in sel} == {"seo", "security"}  # extras need "full"

    def test_extras_excluded_without_full(self):
        sel = select_auditors(["performance"], fake_specs())
        assert all(s[1] == "core" for s in sel)


class TestConcurrency:
    def test_runs_concurrently_not_sequentially(self):
        # 8 auditors × 0.05s each: sequential ≈ 0.40s, concurrent ≈ 0.05-0.10s.
        specs = fake_specs(delay=0.05)
        t0 = time.monotonic()
        results = asyncio.run(gather_auditor_results("https://x.com", ["full"], specs=specs))
        elapsed = time.monotonic() - t0
        assert len(results) == 8
        assert elapsed < 0.25, f"took {elapsed:.3f}s — looks sequential"

    def test_results_keyed_by_name(self):
        results = asyncio.run(gather_auditor_results("https://x.com", ["full"], specs=fake_specs()))
        assert results["seo"].score == len("seo")
        assert results["competitor"].score == len("competitor")


class TestErrorPolicy:
    def test_core_failure_propagates_hard_fail(self):
        specs = fake_specs(fail={"security"})
        try:
            asyncio.run(gather_auditor_results("https://x.com", ["full"], specs=specs))
            assert False, "expected core failure to propagate"
        except RuntimeError as e:
            assert "security boom" in str(e)

    def test_extra_failure_soft_fails_to_none(self):
        specs = fake_specs(fail={"trust"})
        results = asyncio.run(gather_auditor_results("https://x.com", ["full"], specs=specs))
        assert results["trust"] is None          # extra error → None, not a raise
        assert results["mobile_ux"].score == len("mobile_ux")  # siblings unaffected
        assert results["performance"].score == len("performance")  # core unaffected

    def test_only_selected_auditors_run(self):
        ran = []

        def tracking_specs():
            def make(name):
                async def factory(url, mobile, lang):
                    ran.append(name)
                    return FakeResult(1)
                return factory
            return [
                ("performance", "core", "performance", make("performance")),
                ("seo", "core", "seo", make("seo")),
                ("trust", "extra", None, make("trust")),
            ]

        asyncio.run(gather_auditor_results("https://x.com", ["seo"], specs=tracking_specs()))
        assert ran == ["seo"]  # performance not named, trust needs full
