"""Declarative guard rules (#141): a pack's [[guard.deny]] and [[guard.ask]] in pack.toml, evaluated
by core's Claude Code guard hook, so a pack gets its nested-shell unwrapping without a hook of its own.

    [[guard.deny]]
    match = "acme-deploy prod"          # a command: its program, then these words in order
    reason = "deploys to production"

    [[guard.ask]]
    tool = "mcp__acme-jira__*transition*"   # or an MCP tool, as a glob
    reason = "moves an Acme ticket"
    scope = { remotes = ["github.com/acme/*"] }   # optional: in place of the pack's [scope]

`apply` renders every enabled pack's rules, each with its scope, into $BRAINRC_HOME/guard-rules.json,
which overrides/claude/hooks/guard_outward.py reads on each Bash and MCP call. Cursor's, OpenCode's,
Codex's and Antigravity's guards run that hook too (E11, #116), each passing where the command runs.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path

from . import config
from . import scope as pack_scope
from .sources import Source

ACTIONS = ("deny", "ask")
VERSION = 1
# The commands the hook looks past to find the program (its WRAPPERS); tests/test_guard_rules.py
# keeps the two in step.
WRAPPERS = frozenset({"sudo", "doas", "env", "nice", "timeout", "time", "exec", "command", "nohup"})


def rules_file() -> Path:
    return config.settings_home() / "guard-rules.json"


def _table(meta: dict) -> dict:
    g = meta.get("guard")
    return g if isinstance(g, dict) else {}


def words(match: str) -> list[str]:
    """`acme-deploy "prod eu"` -> ['acme-deploy', 'prod eu'], as a shell would split it."""
    return shlex.split(match)


def check(meta: dict, where: str) -> list[str]:
    """Errors in a pack's [guard] the schema can't express: each rule needs exactly one of `match`
    and `tool`, a match the shell can split, and a tool glob that names an MCP tool."""
    errors = []
    for action in ACTIONS:
        rules = _table(meta).get(action)
        for i, rule in enumerate(rules if isinstance(rules, list) else []):
            at = f"{where}: guard.{action}[{i}]"
            if not isinstance(rule, dict):
                continue  # the schema reports it
            has = [k for k in ("match", "tool") if k in rule]
            if len(has) != 1:
                errors.append(f"{at}: set `match` (a command) or `tool` (an MCP tool), one of them")
                continue
            if "match" in rule:
                errors += _match_errors(rule["match"], at)
            if "tool" in rule and not (isinstance(rule["tool"], str) and rule["tool"].startswith("mcp__")):
                errors.append(f"{at}: `tool` must be a string that starts with mcp__ (e.g. mcp__acme-jira__*delete*)")
            errors += pack_scope.check(rule.get("scope"), f"{at}")
    return errors


def _match_errors(match, at: str) -> list[str]:
    if not isinstance(match, str):
        return [f"{at}: `match` must be a string, the command as you'd type it (e.g. \"acme-deploy prod\")"]
    try:
        found = words(match)
    except ValueError as e:
        return [f"{at}: `match` can't be split like a shell command ({e})"]
    if not found:
        return [f"{at}: `match` names no command"]
    if "/" in found[0] or "\\" in found[0]:
        name = found[0].replace("\\", "/").rsplit("/", 1)[-1]
        return [f"{at}: `match` must name the program alone (`{name}`), not a path; it then matches the "
                "program run from any directory"]
    if found[0] in WRAPPERS:
        return [f"{at}: `match` starts with `{found[0]}`; leave it out, since the guard looks past it to "
                "the command it runs"]
    return []


def rules(srcs: list[Source]) -> list[dict]:
    """Every enabled pack's guard rules, in pack then file order, each carrying the scope it runs
    under: its own `scope`, else the pack's [scope], else None (everywhere). A malformed rule is
    left out here; validate names it."""
    found = []
    for src in srcs:
        if src.is_core:
            continue
        default_scope = pack_scope.of(src.meta)
        for action in ACTIONS:
            entries = _table(src.meta).get(action)
            for rule in entries if isinstance(entries, list) else []:
                if not isinstance(rule, dict) or not isinstance(rule.get("reason"), str):
                    continue
                if not check({"guard": {action: [rule]}}, ""):
                    own = rule.get("scope")
                    found.append({
                        "pack": src.name,
                        "action": action,
                        "match": words(rule["match"]) if "match" in rule else None,
                        "tool": rule.get("tool"),
                        "reason": rule["reason"],
                        "scope": own if isinstance(own, dict) else default_scope,
                    })
    return found


def render(srcs: list[Source]) -> str | None:
    """guard-rules.json's text, or None when no enabled pack has a rule (apply then removes it)."""
    found = rules(srcs)
    if not found:
        return None
    return json.dumps({"version": VERSION, "generated_by": "brainrc apply from each pack's pack.toml",
                       "rules": found}, indent=2) + "\n"
