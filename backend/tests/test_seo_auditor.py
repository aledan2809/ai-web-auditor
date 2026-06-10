"""Golden tests — SEOAuditor pure helpers + score model (no network)."""
from bs4 import BeautifulSoup

from auditors.seo import SEOAuditor
from models.schemas import SEOMetrics


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def metrics(**overrides) -> SEOMetrics:
    base = dict(
        score=0,
        title="A perfectly sized page title for testing purposes here",  # 53 chars
        title_length=53,
        meta_description="x" * 155,
        meta_description_length=155,
        h1_count=1,
        h1_texts=["Main heading"],
        canonical_url="https://example.com/",
        robots_txt_exists=True,
        sitemap_exists=True,
        structured_data=[],
        broken_links=[],
        image_alt_missing=0,
    )
    base.update(overrides)
    return SEOMetrics(**base)


aud = SEOAuditor()


class TestHelpers:
    def test_get_title(self):
        assert aud._get_title(soup("<head><title> Hello </title></head>")) == "Hello"

    def test_get_title_missing(self):
        assert aud._get_title(soup("<head></head>")) is None

    def test_get_meta_description(self):
        s = soup('<head><meta name="description" content="My description"></head>')
        assert aud._get_meta_description(s) == "My description"

    def test_get_h1_texts(self):
        s = soup("<h1>First</h1><h2>not me</h2><h1>Second</h1>")
        assert aud._get_h1_texts(s) == ["First", "Second"]

    def test_get_canonical(self):
        s = soup('<head><link rel="canonical" href="https://example.com/page"></head>')
        assert aud._get_canonical(s) == "https://example.com/page"

    def test_count_images_without_alt(self):
        s = soup('<img src="a.png"><img src="b.png" alt=""><img src="c.png" alt="ok">')
        # missing attr counts; empty alt behavior is locked by this golden
        assert aud._count_images_without_alt(s) == 2


class TestScoreModel:
    def test_perfect_page(self):
        overall, tseo, opseo = aud._calculate_score(metrics())
        assert (overall, tseo, opseo) == (100, 100, 100)

    def test_missing_title_costs_25_opseo(self):
        _, _, opseo = aud._calculate_score(metrics(title=None, title_length=0))
        assert opseo == 75

    def test_missing_meta_description_costs_25_opseo(self):
        _, _, opseo = aud._calculate_score(
            metrics(meta_description=None, meta_description_length=0)
        )
        assert opseo == 75

    def test_no_h1_costs_20_multiple_h1_costs_10(self):
        _, _, no_h1 = aud._calculate_score(metrics(h1_count=0, h1_texts=[]))
        _, _, multi = aud._calculate_score(metrics(h1_count=3))
        assert no_h1 == 80
        assert multi == 90

    def test_image_alt_penalty_capped_at_15(self):
        _, _, opseo = aud._calculate_score(metrics(image_alt_missing=50))
        assert opseo == 85

    def test_tseo_penalties(self):
        _, tseo, _ = aud._calculate_score(metrics(robots_txt_exists=False))
        assert tseo == 85
        _, tseo, _ = aud._calculate_score(metrics(sitemap_exists=False))
        assert tseo == 75
        _, tseo, _ = aud._calculate_score(metrics(canonical_url=None))
        assert tseo == 85

    def test_broken_links_capped_at_25(self):
        _, tseo, _ = aud._calculate_score(
            metrics(broken_links=[f"https://x/{i}" for i in range(10)])
        )
        assert tseo == 75

    def test_structured_data_bonus_capped_at_100(self):
        _, tseo, _ = aud._calculate_score(metrics(structured_data=["Organization"]))
        assert tseo == 100  # already 100, bonus must not exceed cap
        _, tseo2, _ = aud._calculate_score(
            metrics(structured_data=["Organization"], robots_txt_exists=False)
        )
        assert tseo2 == 95  # 85 + 10

    def test_overall_is_weighted_60_40(self):
        overall, tseo, opseo = aud._calculate_score(
            metrics(title=None, title_length=0, sitemap_exists=False)
        )
        assert opseo == 75 and tseo == 75
        assert overall == 75
        overall2, _, _ = aud._calculate_score(metrics(title=None, title_length=0))
        assert overall2 == round(75 * 0.6 + 100 * 0.4)  # 85
