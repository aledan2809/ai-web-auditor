"""
Configuration loader for AIWebAuditor
"""

import json
import os
from typing import Dict, Any, List


DEFAULT_CONFIG = {
    "max_depth": 3,
    "timeout": 30,
    "user_agent": "AIWebAuditor/1.0",
    "categories": ["seo", "accessibility", "security", "performance"],
    "accessibility": {"standard": "WCAG_2.1_AA"},
    "performance": {
        "mobile": True,
        "thresholds": {
            "lcp_good": 2.5,
            "lcp_poor": 4.0,
            "cls_good": 0.1,
            "cls_poor": 0.25,
            "ttfb_good": 800,
            "ttfb_poor": 1800,
        },
    },
    "output": {"format": "json", "include_metadata": True},
    "plugins_dir": "plugins",
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from file, falling back to defaults."""
    config = DEFAULT_CONFIG.copy()

    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            user_config = json.load(f)
        config.update(user_config)
    else:
        # Try default locations
        for path in ["config.json", "aiwebauditor/config.json"]:
            if os.path.exists(path):
                with open(path, "r") as f:
                    user_config = json.load(f)
                config.update(user_config)
                break

    return config


def get_enabled_categories(config: Dict[str, Any]) -> List[str]:
    """Get list of enabled audit categories."""
    return config.get("categories", DEFAULT_CONFIG["categories"])
