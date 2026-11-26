#!/usr/bin/env python3
"""Junie hook for PreToolUse (#312): runs the same guards as Claude Code (overrides/claude/hooks),
packs' guard rules included, under their [scope].

Junie sends Claude Code's payload, {"hook_event_name", "tool_name", "tool_input"}, with Claude
Code's tool names (Bash, Read, Write, Edit, Grep), so its calls go to the guards as they are. Its
reply takes {"decision": "ask" | "deny", "reason"}, so an ask stays an ask. A pack's [scope] is
judged from the payload's cwd when it has one, else the directory the hook runs in. Anything this
hook can't handle is allowed: Junie lets a call go ahead when a hook fails, unless you set
`blockOnError`. MCP tool names (mcp__<server>__<tool>) are assumed and untested against a live Junie.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"))
import guard_bridge  # noqa: E402


def claude_calls(payload: dict) -> list[tuple[str, str, dict]]:
    """Junie PreToolUse payload -> (guard, Claude tool name, tool input) calls."""
    tool = payload.get("tool_name") if isinstance(payload.get("tool_name"), str) else ""
    args = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    if tool == "Bash":
        command = args.get("command")
        return guard_bridge.shell_calls(command if isinstance(command, str) else "")
    if tool in ("Read", "Write", "Edit", "Grep"):
        return [(guard_bridge.SECRETS, tool, args)]
    if tool.startswith("mcp__"):
        return [(guard_bridge.OUTWARD, tool, args)]
    return []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) and payload["cwd"] else os.getcwd()
    found = guard_bridge.decide(claude_calls(payload), cwd)
    if found:
        json.dump({"decision": found[0], "reason": found[1]}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
