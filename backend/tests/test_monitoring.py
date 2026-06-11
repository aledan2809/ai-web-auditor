"""Tests — recurring monitoring decision core + one-tick loop (roadmap R3)."""
import asyncio
import json
from datetime import datetime, timezone, timedelta

from services.monitoring import (
    is_due,
    parse_iso,
    score_deltas,
    overall_delta,
    should_notify,
    summarize_deltas,
    build_delta_email,
    run_monitoring_once,
    MIN_OVERALL_DELTA,
)

NOW = datetime(2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc)


class TestCadence:
    def test_never_audited_is_due(self):
        assert is_due(None, "weekly", NOW) is True

    def test_weekly_not_yet_due(self):
        last = (NOW - timedelta(days=3)).isoformat()
        assert is_due(last, "weekly", NOW) is False

    def test_weekly_due_after_7_days(self):
        last = (NOW - timedelta(days=7, minutes=1)).isoformat()
        assert is_due(last, "weekly", NOW) is True

    def test_daily_cadence(self):
        assert is_due((NOW - timedelta(hours=23)).isoformat(), "daily", NOW) is False
        assert is_due((NOW - timedelta(hours=25)).isoformat(), "daily", NOW) is True

    def test_monthly_cadence(self):
        assert is_due((NOW - timedelta(days=29)).isoformat(), "monthly", NOW) is False
        assert is_due((NOW - timedelta(days=31)).isoformat(), "monthly", NOW) is True

    def test_unknown_frequency_defaults_weekly(self):
        assert is_due((NOW - timedelta(days=8)).isoformat(), "fortnightly", NOW) is True

    def test_parse_iso_handles_z_suffix_and_naive(self):
        assert parse_iso("2026-06-01T10:00:00Z").tzinfo is not None
        assert parse_iso("2026-06-01T10:00:00").tzinfo is not None
        assert parse_iso(None) is None
        assert parse_iso("garbage") is None


class TestDeltaMath:
    def test_overall_delta(self):
        assert overall_delta(82, 90) == 8
        assert overall_delta(90, 82) == -8

    def test_score_deltas_only_common_categories(self):
        prev = {"performance": 70, "seo": 90, "security": None}
        curr = {"performance": 65, "seo": 90, "trust": 80}
        ds = {d.key: d for d in score_deltas(prev, curr)}
        assert set(ds) == {"performance", "seo"}  # security None + trust prev-missing excluded
        assert ds["performance"].delta == -5
        assert ds["performance"].direction == "down"
        assert ds["seo"].direction == "flat"

    def test_should_notify_threshold(self):
        assert should_notify(82, 82 + MIN_OVERALL_DELTA) is True
        assert should_notify(82, 82 + MIN_OVERALL_DELTA - 1) is False
        assert should_notify(82, 82 - MIN_OVERALL_DELTA) is True  # drops too
        assert should_notify(None, 95) is False  # first run never notifies here

    def test_summarize_orders_worst_first(self):
        prev = {"performance": 80, "seo": 80}
        curr = {"performance": 60, "seo": 95}
        s = summarize_deltas(score_deltas(prev, curr))
        assert s.index("performance") < s.index("seo")  # -20 before +15

    def test_summarize_no_change(self):
        assert summarize_deltas(score_deltas({"seo": 90}, {"seo": 90})) == "No category changed."


class TestEmail:
    def test_drop_email_subject_and_body(self):
        deltas = score_deltas({"performance": 80, "seo": 90}, {"performance": 60, "seo": 90})
        subject, body = build_delta_email("https://x.com", 85, 75, deltas)
        assert "85→75" in subject and "-10" in subject and "▼" in subject
        assert "performance: 80 → 60 (-20)" in body
        assert "seo" not in body  # flat category not listed

    def test_rise_email(self):
        subject, body = build_delta_email("https://x.com", 70, 88, [])
        assert "▲" in subject and "+18" in subject


def test_run_monitoring_once_audits_due_and_notifies_on_move(tmp_path):
    monitors = [
        {"url": "https://due.com", "email": "a@due.com", "frequency": "weekly",
         "last_audit_at": (NOW - timedelta(days=8)).isoformat(),
         "last_overall": 80, "last_scores": {"seo": 80}},
        {"url": "https://fresh.com", "email": "b@fresh.com", "frequency": "weekly",
         "last_audit_at": (NOW - timedelta(days=1)).isoformat(),
         "last_overall": 90, "last_scores": {"seo": 90}},
    ]
    path = tmp_path / "monitors.json"
    path.write_text(json.dumps(monitors))

    audited_urls = []
    emails = []

    async def fake_audit(url):
        audited_urls.append(url)
        return {"overall": 70, "scores": {"seo": 65}}  # -10 from due.com's 80

    def fake_email(to, subject, body):
        emails.append((to, subject))
        return True

    res = asyncio.run(run_monitoring_once(
        now=NOW, monitors_path=str(path), run_audit=fake_audit, send_email=fake_email,
    ))
    assert res == {"checked": 2, "audited": 1, "notified": 1}
    assert audited_urls == ["https://due.com"]   # fresh.com skipped (not due)
    assert emails[0][0] == "a@due.com"

    # monitor forward-stamped
    saved = json.loads(path.read_text())
    due = next(m for m in saved if m["url"] == "https://due.com")
    assert due["last_overall"] == 70
    assert due["last_audit_at"] == NOW.isoformat()


def test_run_monitoring_once_no_notify_below_threshold(tmp_path):
    monitors = [{
        "url": "https://x.com", "email": "a@x.com", "frequency": "daily",
        "last_audit_at": (NOW - timedelta(days=2)).isoformat(),
        "last_overall": 80, "last_scores": {"seo": 80},
    }]
    path = tmp_path / "m.json"
    path.write_text(json.dumps(monitors))

    async def fake_audit(url):
        return {"overall": 81, "scores": {"seo": 81}}  # +1, below MIN_OVERALL_DELTA

    sent = []
    res = asyncio.run(run_monitoring_once(
        now=NOW, monitors_path=str(path),
        run_audit=fake_audit, send_email=lambda *a: sent.append(a) or True,
    ))
    assert res["audited"] == 1 and res["notified"] == 0
    assert sent == []


def test_run_monitoring_once_empty_source_is_noop(tmp_path):
    """Safety guarantee for activating the loop: absent/empty monitors → no-op."""
    missing = tmp_path / "does-not-exist.json"
    called = {"audit": 0, "email": 0}

    async def fake_audit(url):
        called["audit"] += 1
        return {"overall": 50, "scores": {}}

    res = asyncio.run(run_monitoring_once(
        monitors_path=str(missing),
        run_audit=fake_audit,
        send_email=lambda *a: called.__setitem__("email", called["email"] + 1) or True,
    ))
    assert res == {"checked": 0, "audited": 0, "notified": 0}
    assert called == {"audit": 0, "email": 0}


def test_default_run_audit_and_loop_are_importable():
    from services.monitoring import default_run_audit, run_monitoring_loop
    assert callable(default_run_audit) and callable(run_monitoring_loop)
