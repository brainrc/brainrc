"""Declarative guard rules (#141): a pack's [[guard.deny]] and [[guard.ask]] in pack.toml, evaluated
by core's Claude Code guard hook, so a pack gets its nested-shell unwrapping without a hook of its own.

    [[guard.deny]]
    match = "acme-deploy prod"          # a command: its program, then these words in order
    reason = "deploys to production"

    [[guard.ask]]
    tool = "mcp__acme-jira__*transition*"   # or an MCP tool, as a glob
    reason = "moves an Acme ticket"
    scope = { remotes = ["github.com/acme/*"] }   # optional: in place of the pack's [scope]

    [[guard.deny]]
    path = "~/.acme/credentials"        # or a path, or a host: deny only, compiled to the sandbox
    reason = "holds the Acme deploy key"
    scope = {}                          # sandbox settings apply everywhere, so the rule must too

`apply` renders every enabled pack's command and tool rules, each with its scope, into
$BRAINRC_HOME/guard-rules.json, which overrides/claude/hooks/guard_outward.py reads on each Bash
and MCP call. Cursor's, OpenCode's, Codex's and Antigravity's guards run that hook too (E11, #116),
each passing where the command runs.

`path` and `host` rules (#322) aren't for the hook: apply compiles them into the OS sandbox settings
of each harness that has one (SANDBOXES), where no command can talk its way around them. Claude Code's
sandbox.filesystem.denyRead and denyWrite take the paths, sandbox.network.deniedDomains the hosts.
A sandbox has no notion of where a command runs and can't ask, so these rules are deny-only and apply
everywhere: a pack with a [scope] gives each one `scope = {}`.
"""
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from . import config
from . import scope as pack_scope
from .sources import Source

ACTIONS = ("deny", "ask")
KINDS = ("match", "tool", "path", "host")  # what a rule is about: exactly one per rule
SANDBOX_KINDS = ("path", "host")
VERSION = 1
# Harnesses whose settings file holds an OS sandbox's lists: where each compiled kind goes.
SANDBOXES = {"claude": {"path": [("filesystem", "denyRead"), ("filesystem", "denyWrite")],
                        "host": [("network", "deniedDomains")]}}
HOST = re.compile(r"^(\*\.)?[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*$")
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
            has = [k for k in KINDS if k in rule]
            if len(has) != 1:
                errors.append(f"{at}: set `match` (a command), `tool` (an MCP tool), `path` or `host`, "
                              "one of them")
                continue
            if "match" in rule:
                errors += _match_errors(rule["match"], at)
            if "tool" in rule and not (isinstance(rule["tool"], str) and rule["tool"].startswith("mcp__")):
                errors.append(f"{at}: `tool` must be a string that starts with mcp__ (e.g. mcp__acme-jira__*delete*)")
            if has[0] in SANDBOX_KINDS:
                errors += _sandbox_errors(rule, has[0], action, meta, at)
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


def _sandbox_errors(rule: dict, kind: str, action: str, meta: dict, at: str) -> list[str]:
    """A path or host rule: deny-only, everywhere, and a value a sandbox setting takes."""
    errors = []
    if action != "deny":
        errors.append(f"{at}: a `{kind}` rule goes under [[guard.deny]]: it compiles to the sandbox, "
                      "which can refuse but not ask")
    value = rule[kind]
    if kind == "path" and not (isinstance(value, str) and (value.startswith("~/") or value.startswith("/"))
                               and value.strip("/~")):
        errors.append(f"{at}: `path` must be a string that starts with ~/ or / (e.g. \"~/.acme/credentials\")")
    if kind == "host" and not (isinstance(value, str) and HOST.fullmatch(value)):
        errors.append(f"{at}: `host` must be a domain name, optionally starting with *. (e.g. \"*.acme.example\"), "
                      "with no scheme, port or path")
    own = rule.get("scope")
    effective = own if isinstance(own, dict) else pack_scope.of(meta)
    if not pack_scope.unscoped(effective):
        errors.append(f"{at}: a `{kind}` rule compiles to sandbox settings, which apply everywhere; give it "
                      "`scope = {}` to say so, since the pack's [scope] can't hold there")
    return errors


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
                if any(k in rule for k in SANDBOX_KINDS):
                    continue  # compiled to the sandbox (sandbox()), not checked by the hook
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


def sandbox(srcs: list[Source], harness: str) -> dict:
    """The sandbox lists every enabled pack's path and host rules compile to in harness's settings
    file: {"filesystem": {"denyRead": [...], ...}, "network": {...}}; {} when the harness has no
    sandbox or no pack has such a rule. A malformed rule is left out here; validate names it."""
    targets = SANDBOXES.get(harness)
    out: dict[str, dict[str, list[str]]] = {}
    for src in srcs if targets else []:
        if src.is_core:
            continue
        entries = _table(src.meta).get("deny")
        for rule in entries if isinstance(entries, list) else []:
            kind = next((k for k in SANDBOX_KINDS if isinstance(rule, dict) and k in rule), None)
            alone = {"guard": {"deny": [rule]}, "scope": src.meta.get("scope")}  # the pack's scope counts
            if kind is None or not isinstance(rule.get("reason"), str) or check(alone, ""):
                continue
            for section, key in targets[kind]:
                found = out.setdefault(section, {}).setdefault(key, [])
                if rule[kind] not in found:
                    found.append(rule[kind])
    return out
