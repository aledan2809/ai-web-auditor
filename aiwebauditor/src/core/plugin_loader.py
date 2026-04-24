"""
Plugin loader - Dynamically loads audit rules from the plugins directory
"""

import importlib.util
import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from ..schemas.models import AuditCategory, AuditIssue, Severity

logger = logging.getLogger("aiwebauditor")


class PluginRule:
    """Represents a single audit rule from a plugin."""

    def __init__(
        self,
        name: str,
        category: AuditCategory,
        severity: Severity,
        title: str,
        description: str,
        recommendation: str,
        check_fn: Callable,
        estimated_hours: float = 1.0,
        complexity: str = "medium",
    ):
        self.name = name
        self.category = category
        self.severity = severity
        self.title = title
        self.description = description
        self.recommendation = recommendation
        self.check_fn = check_fn
        self.estimated_hours = estimated_hours
        self.complexity = complexity


def load_plugins(plugins_dir: str) -> List[PluginRule]:
    """Load all plugins from the specified directory."""
    rules: List[PluginRule] = []

    if not os.path.isdir(plugins_dir):
        logger.debug(f"Plugins directory not found: {plugins_dir}")
        return rules

    for filename in sorted(os.listdir(plugins_dir)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        filepath = os.path.join(plugins_dir, filename)
        module_name = filename[:-3]

        try:
            spec = importlib.util.spec_from_file_location(
                f"aiwebauditor.plugins.{module_name}", filepath
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for RULES list in module
            if hasattr(module, "RULES"):
                for rule_def in module.RULES:
                    check_fn_name = rule_def.get("check_function")
                    check_fn = getattr(module, check_fn_name, None)
                    if check_fn is None:
                        logger.warning(
                            f"Plugin {filename}: check function '{check_fn_name}' not found"
                        )
                        continue

                    rule = PluginRule(
                        name=rule_def["name"],
                        category=AuditCategory(rule_def["category"]),
                        severity=Severity(rule_def.get("severity", "medium")),
                        title=rule_def.get("title", rule_def["name"]),
                        description=rule_def.get("description", ""),
                        recommendation=rule_def.get("recommendation", ""),
                        check_fn=check_fn,
                        estimated_hours=rule_def.get("estimated_hours", 1.0),
                        complexity=rule_def.get("complexity", "medium"),
                    )
                    rules.append(rule)
                    logger.info(f"Loaded plugin rule: {rule.name} from {filename}")

        except Exception as e:
            logger.error(f"Failed to load plugin {filename}: {e}")

    logger.info(f"Total plugin rules loaded: {len(rules)}")
    return rules


def run_plugin_rules(rules: List[PluginRule], html: str, url: str) -> List[AuditIssue]:
    """Run all plugin rules against HTML content."""
    issues: List[AuditIssue] = []

    for rule in rules:
        try:
            result = rule.check_fn(html, url)
            if result:
                # result can be True (issue found) or a string (custom description)
                desc = result if isinstance(result, str) else rule.description
                issues.append(AuditIssue(
                    id=f"plugin_{rule.name}_{hash(url) % 100000}",
                    category=rule.category,
                    severity=rule.severity,
                    title=rule.title,
                    description=desc,
                    recommendation=rule.recommendation,
                    estimated_hours=rule.estimated_hours,
                    complexity=rule.complexity,
                ))
        except Exception as e:
            logger.error(f"Plugin rule '{rule.name}' failed: {e}")

    return issues
