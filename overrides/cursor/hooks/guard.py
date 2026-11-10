#!/usr/bin/env python3
"""Cursor hook for beforeShellExecution and beforeReadFile: runs the same guards as Claude Code
(overrides/claude/hooks) and replies in Cursor's format.

Cursor's `ask` is unreliable for shell commands and not accepted for reads, so an "ask" denies
too; the agent gets the reason and should ask the user to run it themselves. Anything this hook
can't handle (bad input, a guard that fails to run) is allowed, as a broken Claude hook is.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
HOOKS = Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"


def claude_calls(event: dict) -> list[tuple[str, dict, str]]:
    """Cursor event -> (guard, Claude tool name, tool input) calls the guards understand."""
    name = event.get("hook_event_name")
    if name == "beforeShellExecution":
        bash = {"command": str(event.get("command") or "")}
        return [("guard_outward.py", "Bash", bash), ("guard_secrets.py", "Bash", bash)]
    if name == "beforeReadFile":
        return [("guard_secrets.py", "Read", {"file_path": str(event.get("file_path") or "")})]
    return []


def objection(guard: str, tool: str, tool_input: dict) -> str | None:
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input})
    try:
        run = subprocess.run([sys.executable, str(HOOKS / guard)], input=payload, capture_output=True,
                             text=True, timeout=5)
        decision = json.loads(run.stdout).get("hookSpecificOutput", {}) if run.stdout.strip() else {}
    except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
        return None
    if run.returncode == 0 and decision.get("permissionDecision") in ("ask", "deny"):
        return str(decision.get("permissionDecisionReason") or "brainrc's guard objected.")
    return None


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    reply = {"permission": "allow"}
    for guard, tool, tool_input in claude_calls(event if isinstance(event, dict) else {}):
        reason = objection(guard, tool, tool_input)
        if reason:
            message = (f"{reason} Cursor can't reliably ask for approval, so this is blocked; "
                       "ask the user to run it themselves.")
            reply = {"permission": "deny", "user_message": message, "agent_message": message}
            break
    print(json.dumps(reply))


if __name__ == "__main__":
    main()
