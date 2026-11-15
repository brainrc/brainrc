"""Starter profiles for `brainrc init` (#297), and the counts init shows before it writes.

A starter profile is a first answer to "what should this machine install": an install profile
(`minimal`, `recommended`, `full`; docs/install.md) plus the `exclude` patterns that fit the work.

- minimal: the rules only.
- app: skills, agents, commands and hooks, without the infrastructure domain skills.
- infra: everything, MCP servers included.
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from .config import PROFILES, TABLE_HEADER
from .sources import Source, excluded, frontmatter, local_rules, markdown_files, rule_text, skills
from .tokens import estimate_tokens

# Gatework's infrastructure domain skills (docs/spec-agent.md § Domain skills).
INFRA_SKILLS = ("brainrc-terraform", "brainrc-aws", "brainrc-kubernetes", "brainrc-gitops")
APP_EXCLUDE = tuple(f"gatework:skills/{s}" for s in INFRA_SKILLS)
STARTERS: dict[str, tuple[str, tuple[str, ...]]] = {
    "minimal": ("minimal", ()),
    "app": ("recommended", APP_EXCLUDE),
    "infra": ("full", ()),
}
STARTER_HELP = {"minimal": "rules only", "app": "skills, agents, commands and hooks; no infra skills",
                "infra": "everything, MCP servers included"}
MANAGED = frozenset(p for _, patterns in STARTERS.values() for p in patterns)  # patterns a starter owns


def _top_level(lines: list[str]) -> int:
    """Index of the first table header: top-level keys sit above it."""
    return next((i for i, raw in enumerate(lines) if TABLE_HEADER.match(raw)), len(lines))


def set_exclude(text: str, patterns: list[str]) -> str:
    """text (a brainrc.local.toml) with its top-level `exclude` set to patterns (removed when there
    are none), everything else kept as is. A multi-line array is replaced whole."""
    line = "exclude = [" + ", ".join(json.dumps(p) for p in patterns) + "]\n" if patterns else ""
    lines = text.splitlines(keepends=True)
    for i in range(_top_level(lines)):
        if re.match(r"\s*exclude\s*=", lines[i]):
            end = i
            if "]" not in lines[i].split("#", 1)[0]:  # an array over several lines
                end = next((j for j in range(i + 1, len(lines)) if "]" in lines[j].split("#", 1)[0]), i)
            lines[i:end + 1] = [line]
            return "".join(lines)
    if not line:
        return text
    at = next((i + 1 for i in range(_top_level(lines)) if re.match(r"\s*profile\s*=", lines[i])), 0)
    lines.insert(at, line)
    return "".join(lines)


def starter_text(text: str, starter: str) -> str:
    """brainrc.local.toml with the starter's profile, and its exclude patterns in place of another
    starter's; patterns the user added stay."""
    from .init import set_profile
    profile, patterns = STARTERS[starter]
    try:
        current = tomllib.loads(text).get("exclude", [])
    except tomllib.TOMLDecodeError:
        current = []
    mine = [p for p in current if isinstance(p, str) and p not in MANAGED] if isinstance(current, list) else []
    return set_exclude(set_profile(text, profile), [*mine, *(p for p in patterns if p not in mine)])


def _hooks_in(fragment: Path) -> int:
    """Hook commands in a settings fragment: every object with a `command`."""
    try:
        data = json.loads(fragment.read_text())
    except (OSError, json.JSONDecodeError):
        return 0

    def walk(node) -> int:
        if isinstance(node, dict):
            return ("command" in node) + sum(walk(v) for v in node.values())
        return sum(walk(v) for v in node) if isinstance(node, list) else 0
    return walk(data.get("hooks", {}))


def hook_count(srcs: list[Source], harnesses: dict[str, dict], profile: str) -> dict[str, int]:
    """Hooks apply installs per harness: the sources' fragments for each harness with a hooks dir."""
    if "hooks" not in PROFILES[profile]:
        return {}
    found = {}
    for name, h in harnesses.items():
        if "hooks_dir" not in h:
            continue
        n = sum(_hooks_in(s.root / "overrides" / name / "settings.fragment.json") for s in srcs)
        if n:
            found[name] = n
    return found


def always_tokens(srcs: list[Source], profile: str, exclude: list[str],
                  extra_rules: list[str], extra_descriptions: list[str]) -> tuple[int, int]:
    """(rule tokens, description tokens) every session loads after apply: every source's rules and
    machine-local rules, plus the descriptions of the items the profile installs."""
    rules = sum(estimate_tokens(rule_text(p)) for s in srcs for p in markdown_files("rules", s))
    rules += sum(estimate_tokens(rule_text(p)) for p in local_rules(srcs))
    rules += sum(estimate_tokens(t) for t in extra_rules)
    descriptions = sum(estimate_tokens(d) for d in extra_descriptions)
    if "items" in PROFILES[profile]:
        for s in srcs:
            paths = [p / "SKILL.md" for p in skills(s) if not excluded(s, p, exclude)]
            paths += [p for kind in ("agents", "commands") for p in markdown_files(kind, s)
                      if not excluded(s, p, exclude)]
            descriptions += sum(estimate_tokens(frontmatter(p).get("description", "")) for p in paths)
    return rules, descriptions
