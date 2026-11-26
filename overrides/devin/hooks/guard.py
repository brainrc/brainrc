#!/usr/bin/env python3
"""Devin Local hook for PreToolUse (#309): runs the same guards as Claude Code
(overrides/claude/hooks), packs' guard rules included, under their [scope].

Devin sends {"tool_name", "tool_input", ...} with Claude Code's event names but its own tools:
exec runs tool_input.command; read, write and edit take a file path (`file_path`, or `path`);
write's text is `content`, edit's `new_string`; MCP tools are mcp__<server>__<tool>, as Claude
Code names them. Its payload carries no cwd, so a pack's [scope] is judged from
$DEVIN_PROJECT_DIR, else the directory the hook runs in. {"decision": "block"} blocks the call;
Devin has no "ask", so an ask blocks too and the agent is told to ask the user to run it
themselves. Anything this hook can't handle is allowed, as a failing hook is. The file fields
are inferred (Devin's docs name only exec's) and untested against a live Devin.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"))
import guard_bridge  # noqa: E402


def text(value) -> str:
    return value if isinstance(value, str) else ""


def claude_calls(payload: dict) -> list[tuple[str, str, dict]]:
    """Devin PreToolUse payload -> (guard, Claude tool name, tool input) calls."""
    tool = text(payload.get("tool_name"))
    args = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    path = text(args.get("file_path")) or text(args.get("path"))
    if tool == "exec":
        return guard_bridge.shell_calls(text(args.get("command")))
    if tool == "read":
        return guard_bridge.read_call(path)
    if tool == "write":
        return guard_bridge.write_call(path, text(args.get("content")))
    if tool == "edit":
        return guard_bridge.write_call(path, text(args.get("new_string")))
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
    cwd = text(payload.get("cwd")) or os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    found = guard_bridge.decide(claude_calls(payload), cwd)
    if found:
        json.dump({"decision": "block", "reason": guard_bridge.blocked(*found, "Devin")}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
