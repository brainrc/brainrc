#!/usr/bin/env python3
"""Kiro hook for PreToolUse (#310): runs the same guards as Claude Code (overrides/claude/hooks),
packs' guard rules included, under their [scope] judged from `cwd`.

Kiro sends {"hook_event_name", "cwd", "tool_name", "tool_input", ...}. A command hook that exits
non-zero blocks the call and its stderr goes to the agent; Kiro's PreToolUse has no "ask", so an
ask blocks too and the agent is told to ask the user to run it themselves. This hook exits 0 for
anything it can't handle, since any other exit would block the call. Shell is execute_bash or
execute_pwsh with tool_input.command; reads (fs_read, read_file) take a `path`, or `operations`
holding paths; writes (fs_write, fs_append, str_replace) a `path` and `file_text`, `new_str` or
`content`; MCP tools are mcp_<server>_<tool>. Kiro's docs show its tool ids only in examples, so
the fields are inferred and untested against a live Kiro.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"))
import guard_bridge  # noqa: E402

SHELLS = ("execute_bash", "execute_pwsh")
READS = ("fs_read", "read_file")
WRITES = ("fs_write", "fs_append", "str_replace")


def text(value) -> str:
    return value if isinstance(value, str) else ""


def claude_calls(payload: dict) -> list[tuple[str, str, dict]]:
    """Kiro PreToolUse payload -> (guard, Claude tool name, tool input) calls."""
    tool = text(payload.get("tool_name"))
    args = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    path = text(args.get("path"))
    if tool in SHELLS:
        return guard_bridge.shell_calls(text(args.get("command")))
    if tool in READS:
        ops = args.get("operations") if isinstance(args.get("operations"), list) else []
        paths = [path] + [text(op.get("path")) for op in ops if isinstance(op, dict)]
        return [c for p in paths for c in guard_bridge.read_call(p)]
    if tool in WRITES:
        written = text(args.get("file_text")) or text(args.get("new_str")) or text(args.get("content"))
        return guard_bridge.write_call(path, written)
    if tool.startswith("mcp_"):
        server, _, name = tool[len("mcp_"):].partition("_")
        return guard_bridge.mcp_call(server, name, args)
    return []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
    found = guard_bridge.decide(claude_calls(payload), cwd)
    if found:
        print(guard_bridge.blocked(*found, "Kiro"), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
