"""
Example plugin: Additional SEO checks
Place .py files in the plugins/ directory to extend AIWebAuditor.

Each plugin must define a RULES list and the corresponding check functions.
"""

from bs4 import BeautifulSoup

# Rule definitions - must match rules_schema.json
RULES = [
    {
        "name": "seo_og_tags",
        "category": "seo",
        "severity": "medium",
        "title": "Missing Open Graph tags",
        "description": "Open Graph tags are missing, limiting social media sharing previews.",
        "recommendation": "Add og:title, og:description, og:image meta tags.",
        "check_function": "check_og_tags",
        "estimated_hours": 1.0,
        "complexity": "simple",
    },
    {
        "name": "seo_twitter_cards",
        "category": "seo",
        "severity": "low",
        "title": "Missing Twitter Card tags",
        "description": "Twitter Card meta tags are not present.",
        "recommendation": "Add twitter:card, twitter:title, twitter:description meta tags.",
        "check_function": "check_twitter_cards",
        "estimated_hours": 0.5,
        "complexity": "simple",
    },
]


def check_og_tags(html: str, url: str) -> bool:
    """Check if Open Graph meta tags are present."""
    soup = BeautifulSoup(html, "lxml")
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_image = soup.find("meta", attrs={"property": "og:image"})

    # Return True if any are missing (= issue found)
    return not (og_title and og_desc and og_image)


def check_twitter_cards(html: str, url: str) -> bool:
    """Check if Twitter Card meta tags are present."""
    soup = BeautifulSoup(html, "lxml")
    tc = soup.find("meta", attrs={"name": "twitter:card"})
    return tc is None
