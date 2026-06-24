"""Golden tests — GDPRAuditor pure helpers + score model (no network)."""
from bs4 import BeautifulSoup

from auditors.gdpr import GDPRAuditor
from models.schemas import GDPRMetrics


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def metrics(**overrides) -> GDPRMetrics:
    base = dict(
        score=0,
        cookie_banner_present=True,
        privacy_policy_link=True,
        cookie_categories_explained=True,
        opt_out_option=True,
        third_party_trackers=[],
        google_analytics=False,
        facebook_pixel=False,
        data_retention_info=True,
    )
    base.update(overrides)
    return GDPRMetrics(**base)


aud = GDPRAuditor()


class TestCookieBannerDetection:
    def test_class_based_banner(self):
        s = soup('<div class="cookie-consent-banner">We use cookies</div>')
        assert aud._detect_cookie_banner(s, str(s)) is True

    def test_gdpr_class(self):
        s = soup('<section class="gdpr-notice">…</section>')
        assert aud._detect_cookie_banner(s, str(s)) is True

    def test_clean_page(self):
        s = soup("<div class='hero'>Welcome to our site</div>")
        assert aud._detect_cookie_banner(s, str(s)) is False


class TestTrackers:
    def test_google_analytics_detected(self):
        content = '<script src="https://www.googletagmanager.com/gtag/js?id=G-ABC123"></script>'
        assert aud._has_tracker(content, aud.tracking_patterns["google_analytics"]) is True

    def test_no_trackers(self):
        assert aud._has_tracker("<p>hello</p>", aud.tracking_patterns["google_analytics"]) is False

    def test_ga4_bare_id_detected(self):
        # GA4 measurement ID present without gtag.js src (real config) still detected
        content = '<script>window.dataLayer=[];gtagId="G-ABC1234567";</script>'
        assert aud._has_tracker(content, aud.tracking_patterns["google_analytics"]) is True

    def test_css_class_not_false_positive(self):
        # Regression: r'G-[A-Z0-9]+' under re.I matched "g-transparent" (from
        # class="bg-transparent") → false GA=True on tracker-free pages.
        content = '<input class="flex-1 bg-transparent text-white" />'
        assert aud._has_tracker(content, aud.tracking_patterns["google_analytics"]) is False


class TestScoreModel:
    def test_all_good_is_100(self):
        assert aud._calculate_score(metrics()) == 100

    def test_no_banner_without_trackers_is_100(self):
        # Cookieless site needs no consent banner → no penalty (false-positive fix).
        assert aud._calculate_score(metrics(cookie_banner_present=False)) == 100

    def test_cookieless_site_no_consent_ui_is_100(self):
        # No trackers + no banner + no categories + no opt-out → still 100:
        # consent UI is irrelevant when nothing non-essential is loaded.
        m = metrics(
            cookie_banner_present=False,
            cookie_categories_explained=False,
            opt_out_option=False,
            third_party_trackers=[],
        )
        assert aud._calculate_score(m) == 100

    def test_no_banner_with_trackers_costs_30_plus_15(self):
        m = metrics(cookie_banner_present=False, third_party_trackers=["ga"])
        assert aud._calculate_score(m) == 55

    def test_no_privacy_policy_costs_25(self):
        # Privacy-policy penalty is unconditional (personal data via forms/accounts).
        assert aud._calculate_score(metrics(privacy_policy_link=False)) == 75

    def test_consent_ui_quality_penalties(self):
        # Quality penalties apply only when trackers are present (banner shown).
        assert aud._calculate_score(metrics(third_party_trackers=["ga"], cookie_categories_explained=False)) == 90
        assert aud._calculate_score(metrics(third_party_trackers=["ga"], opt_out_option=False)) == 90

    def test_floor_at_zero(self):
        worst = metrics(
            cookie_banner_present=False,
            privacy_policy_link=False,
            cookie_categories_explained=False,
            opt_out_option=False,
            third_party_trackers=["ga", "fb"],
        )
        assert aud._calculate_score(worst) == 10  # 100-30-25-10-10-15
