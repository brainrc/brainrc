#!/usr/bin/env python3
"""Cursor hook for beforeShellExecution and beforeReadFile: runs the same guards as Claude Code
(overrides/claude/hooks), packs' guard rules included, and replies in Cursor's format.

A pack's [[guard.deny]] applies under its [scope], judged from the event's `cwd` (else the first
workspace root). Cursor's `ask` is unreliable for shell commands and not accepted for reads, so an
"ask" denies too; the agent gets the reason and should ask the user to run it themselves. Anything
this hook can't handle (bad input, a guard that fails to run) is allowed, as a broken Claude hook is.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"))
import guard_bridge  # noqa: E402


def claude_calls(event: dict) -> list[tuple[str, str, dict]]:
    """Cursor event -> (guard, Claude tool name, tool input) calls the guards understand."""
    name = event.get("hook_event_name")
    if name == "beforeShellExecution":
        return guard_bridge.shell_calls(str(event.get("command") or ""))
    if name == "beforeReadFile":
        return [(guard_bridge.SECRETS, "Read", {"file_path": str(event.get("file_path") or "")})]
    return []


def where(event: dict) -> str | None:
    """The directory the command runs in: Cursor's `cwd`, else the first workspace root."""
    if isinstance(event.get("cwd"), str) and event["cwd"]:
        return event["cwd"]
    roots = event.get("workspace_roots")
    return roots[0] if isinstance(roots, list) and roots and isinstance(roots[0], str) else None


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    event = event if isinstance(event, dict) else {}
    found = guard_bridge.decide(claude_calls(event), where(event))
    reply = {"permission": "allow"}
    if found:
        message = guard_bridge.blocked(*found, "Cursor")
        reply = {"permission": "deny", "user_message": message, "agent_message": message}
    print(json.dumps(reply))


if __name__ == "__main__":
    main()
