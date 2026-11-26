#!/usr/bin/env python3
"""Antigravity hook for PreToolUse: runs the same guards as Claude Code (overrides/claude/hooks),
packs' guard rules included, on each run_command, and replies in Antigravity's format.

Antigravity sends {"toolCall": {"name", "args"}, "workspacePaths", ...}; a shell command is
run_command with args.CommandLine, run in args.Cwd (else the first workspace path), which is where a
pack's [scope] is judged. Every reply needs a decision. "allow" is the one that changes nothing: its
docs say it hands the call on to the next hook or the default policy, so your own permission
settings still decide (unlike "auto_approve"). A guard's ask is "force_ask", which prompts even
for a command you allowed before, and a deny is "deny". Anything this hook can't handle replies
"allow", as a broken hook leaves the call to the default policy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"))
import guard_bridge  # noqa: E402

REPLY = {"deny": "deny", "ask": "force_ask"}


def claude_calls(call: dict) -> list[tuple[str, str, dict]]:
    """Antigravity tool call -> (guard, Claude tool name, tool input) calls the guards understand."""
    args = call.get("args") if isinstance(call.get("args"), dict) else {}
    if call.get("name") == "run_command":
        return guard_bridge.shell_calls(str(args.get("CommandLine") or ""))
    return []


def where(payload: dict, call: dict) -> str | None:
    """The directory the command runs in: args.Cwd, else the first workspace path."""
    args = call.get("args") if isinstance(call.get("args"), dict) else {}
    if isinstance(args.get("Cwd"), str) and args["Cwd"]:
        return args["Cwd"]
    roots = payload.get("workspacePaths")
    return roots[0] if isinstance(roots, list) and roots and isinstance(roots[0], str) else None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    call = payload.get("toolCall") if isinstance(payload.get("toolCall"), dict) else {}
    found = guard_bridge.decide(claude_calls(call), where(payload, call))
    reply = {"decision": "allow"}
    if found:
        decision, reason = found
        reply = {"decision": REPLY[decision], "reason": reason}
    print(json.dumps(reply))


if __name__ == "__main__":
    main()
