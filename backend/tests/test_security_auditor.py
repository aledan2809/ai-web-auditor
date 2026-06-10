"""Golden tests — SecurityAuditor pure helpers + score model (no network)."""
from auditors.security import SecurityAuditor
from models.schemas import SecurityMetrics


def metrics(**overrides) -> SecurityMetrics:
    base = dict(
        score=0,
        https_enabled=True,
        ssl_valid=True,
        ssl_expiry_days=90,
        hsts_enabled=True,
        csp_enabled=True,
        x_frame_options=True,
        x_content_type_options=True,
        cookies_secure=True,
        cookies_httponly=True,
        exposed_emails=[],
        exposed_api_keys=False,
    )
    base.update(overrides)
    return SecurityMetrics(**base)


aud = SecurityAuditor()


class TestFindEmails:
    def test_finds_and_dedups(self):
        content = "contact a@b.ro or a@b.ro and also x@y.com"
        assert sorted(aud._find_emails(content)) == ["a@b.ro", "x@y.com"]

    def test_filters_image_false_positives(self):
        content = "logo@2x.png hero@large.jpg real@mail.com"
        assert aud._find_emails(content) == ["real@mail.com"]

    def test_empty_content(self):
        assert aud._find_emails("no emails here") == []


class TestExposedKeys:
    def test_openai_key(self):
        assert aud._check_exposed_keys('const k = "sk-' + "a" * 24 + '"') is True

    def test_stripe_live_key(self):
        assert aud._check_exposed_keys("pk_live_" + "b" * 24) is True

    def test_google_api_key(self):
        assert aud._check_exposed_keys("AIza" + "c" * 35) is True

    def test_api_key_assignment(self):
        assert aud._check_exposed_keys('api_key = "' + "d" * 24 + '"') is True

    def test_clean_content(self):
        assert aud._check_exposed_keys("just a normal page about apis") is False


class TestScoreModel:
    def test_all_good_is_100(self):
        assert aud._calculate_score(metrics()) == 100

    def test_no_https_costs_25(self):
        assert aud._calculate_score(metrics(https_enabled=False)) == 75

    def test_invalid_ssl_costs_20(self):
        assert aud._calculate_score(metrics(ssl_valid=False)) == 80

    def test_expiring_ssl_costs_10_only_when_valid(self):
        assert aud._calculate_score(metrics(ssl_expiry_days=10)) == 90
        # invalid SSL takes the -20 branch; expiry not double-counted
        assert aud._calculate_score(metrics(ssl_valid=False, ssl_expiry_days=10)) == 80

    def test_header_penalties(self):
        assert aud._calculate_score(metrics(hsts_enabled=False)) == 90
        assert aud._calculate_score(metrics(csp_enabled=False)) == 90
        assert aud._calculate_score(metrics(x_frame_options=False)) == 95
        assert aud._calculate_score(metrics(x_content_type_options=False)) == 95

    def test_exposed_data_penalties(self):
        assert aud._calculate_score(metrics(exposed_api_keys=True)) == 85
        assert aud._calculate_score(metrics(exposed_emails=["a@b.ro"])) == 95

    def test_floor_at_zero(self):
        worst = metrics(
            https_enabled=False,
            ssl_valid=False,
            hsts_enabled=False,
            csp_enabled=False,
            x_frame_options=False,
            x_content_type_options=False,
            cookies_secure=False,
            exposed_api_keys=True,
            exposed_emails=["a@b.ro"],
        )
        assert aud._calculate_score(worst) == 0
