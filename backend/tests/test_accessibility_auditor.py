"""Golden tests — AccessibilityAuditor pure helpers + score model (no network)."""
from bs4 import BeautifulSoup

from auditors.accessibility import AccessibilityAuditor
from models.schemas import AccessibilityMetrics


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def metrics(**overrides) -> AccessibilityMetrics:
    base = dict(
        score=0,
        wcag_level="AA",
        color_contrast_issues=0,
        missing_alt_texts=0,
        missing_form_labels=0,
        keyboard_navigation=True,
        aria_usage=0,
        heading_hierarchy_valid=True,
    )
    base.update(overrides)
    return AccessibilityMetrics(**base)


aud = AccessibilityAuditor()


class TestHelpers:
    def test_check_form_labels_counts_unlabeled(self):
        s = soup(
            """
            <form>
              <input type="text" id="a">
              <label for="b">B</label><input type="text" id="b">
              <input type="text" aria-label="c">
              <label>Wrapped <input type="text"></label>
              <input type="text" placeholder="d">
              <input type="hidden" name="csrf">
              <input type="submit" value="Go">
            </form>
            """
        )
        # only the first input has no label/aria/wrap/placeholder
        assert aud._check_form_labels(s) == 1

    def test_language_attribute(self):
        assert aud._check_language_attribute(soup('<html lang="ro"><body></body></html>')) is True
        assert aud._check_language_attribute(soup("<html><body></body></html>")) is False

    def test_skip_links_visible_and_sr_only(self):
        visible = soup('<a href="#main">Skip to content</a>')
        sr_only = soup('<a href="#main-content" class="sr-only">Sari la conținut</a>')
        none = soup('<a href="/about">About</a>')
        assert aud._check_skip_links(visible) is True
        assert aud._check_skip_links(sr_only) is True
        assert aud._check_skip_links(none) is False


class TestScoreModel:
    def test_perfect_page(self):
        assert aud._calculate_score(metrics(), has_lang=True, has_skip=True) == 100

    def test_alt_text_penalty_capped_at_20(self):
        assert aud._calculate_score(metrics(missing_alt_texts=2), True, True) == 94
        assert aud._calculate_score(metrics(missing_alt_texts=50), True, True) == 80

    def test_form_label_penalty_capped_at_15(self):
        assert aud._calculate_score(metrics(missing_form_labels=1), True, True) == 95
        assert aud._calculate_score(metrics(missing_form_labels=10), True, True) == 85

    def test_heading_hierarchy_costs_10(self):
        assert aud._calculate_score(metrics(heading_hierarchy_valid=False), True, True) == 90

    def test_lang_and_skip_penalties(self):
        assert aud._calculate_score(metrics(), has_lang=False, has_skip=True) == 90
        assert aud._calculate_score(metrics(), has_lang=True, has_skip=False) == 95

    def test_keyboard_navigation_costs_10(self):
        assert aud._calculate_score(metrics(keyboard_navigation=False), True, True) == 90

    def test_aria_bonus_capped_at_100(self):
        assert aud._calculate_score(metrics(aria_usage=5), True, True) == 100
        assert (
            aud._calculate_score(metrics(aria_usage=5, heading_hierarchy_valid=False), True, True)
            == 95
        )

    def test_floor_at_zero(self):
        worst = metrics(
            missing_alt_texts=99,
            missing_form_labels=99,
            color_contrast_issues=99,
            keyboard_navigation=False,
            heading_hierarchy_valid=False,
        )
        assert aud._calculate_score(worst, has_lang=False, has_skip=False) == 15
