#!/usr/bin/env python3
"""GitHub Copilot hook for preToolUse (#307): runs the same guards as Claude Code
(overrides/claude/hooks), packs' guard rules included, under their [scope] judged from `cwd`.

The Copilot CLI sends {"toolName", "toolArgs", "cwd", ...}; toolArgs is the call's arguments as a
JSON string (an object is read too). Shell is bash or powershell with a `command`; view reads a
`path`; create writes `file_text` and edit, str_replace_editor write `new_str` to a `path`. A
reply of {"permissionDecision": "deny"} blocks the call; Copilot acts on no "ask", so an ask denies
here and the agent is told to ask the user to run it themselves. No objection prints nothing,
which leaves Copilot's own permission prompts in charge. Anything this hook can't handle is allowed.
The deny reply and the tool names come from Copilot's hooks reference and are untested against a
live Copilot CLI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"))
import guard_bridge  # noqa: E402

SHELLS = ("bash", "powershell")
EDITS = ("edit", "str_replace_editor")


def text(value) -> str:
    return value if isinstance(value, str) else ""


def arguments(value) -> dict:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def claude_calls(payload: dict) -> list[tuple[str, str, dict]]:
    """Copilot preToolUse payload -> (guard, Claude tool name, tool input) calls."""
    tool = text(payload.get("toolName"))
    args = arguments(payload.get("toolArgs"))
    path = text(args.get("path"))
    if tool in SHELLS:
        return guard_bridge.shell_calls(text(args.get("command")))
    if tool == "view":
        return guard_bridge.read_call(path)
    if tool == "create":
        return guard_bridge.write_call(path, text(args.get("file_text")))
    if tool in EDITS:
        return guard_bridge.write_call(path, text(args.get("new_str")))
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
        json.dump({"permissionDecision": "deny",
                   "permissionDecisionReason": guard_bridge.blocked(*found, "Copilot")}, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:  # noqa: BLE001: a hook that fails blocks the call here, so fail open instead
        code = 0
    sys.exit(code)
