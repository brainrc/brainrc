#!/usr/bin/env python3
"""Codex hook for PreToolUse: runs the same guards as Claude Code (overrides/claude/hooks), packs'
guard rules included, under their [scope] judged from the payload's `cwd`.

Codex sends Claude Code's payload shape: shell commands (and unified exec) as tool_name "Bash",
file edits as "apply_patch" with the patch in tool_input.command, and MCP tools as mcp__<server>__<tool>.
Its PreToolUse takes "allow" and "deny" only: an "ask" counts as a failed hook and the call goes
ahead, so an ask denies here too and the agent is told to ask the user to run it themselves. No
objection prints nothing, which leaves Codex's own approval policy in charge. Anything this hook
can't handle is allowed, as a broken hook is.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# brainrc links this directory; resolve the link so the guards are found in a checkout or a package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"))
import guard_bridge  # noqa: E402

FILE_HEADERS = ("*** Add File: ", "*** Update File: ", "*** Move to: ")


def patch_files(patch: str) -> list[tuple[str, str]]:
    """(path, added lines) for each file an apply_patch adds, changes or moves to."""
    files: list[tuple[str, list[str]]] = []
    for line in patch.splitlines():
        header = next((h for h in FILE_HEADERS if line.startswith(h)), None)
        if header:
            files.append((line[len(header):].strip(), files[-1][1] if header == FILE_HEADERS[2] and files else []))
        elif line.startswith("*** "):
            continue
        elif line.startswith("+") and files:
            files[-1][1].append(line[1:])
    return [(path, "\n".join(added)) for path, added in files if path]


def claude_calls(payload: dict) -> list[tuple[str, str, dict]]:
    """Codex PreToolUse payload -> (guard, Claude tool name, tool input) calls the guards understand."""
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    if tool == "Bash":
        return guard_bridge.shell_calls(str(tool_input.get("command") or ""))
    if tool.startswith("mcp__"):
        return [(guard_bridge.OUTWARD, tool, tool_input)]
    if tool == "apply_patch":
        return [(guard_bridge.SECRETS, "Write", {"file_path": path, "content": added})
                for path, added in patch_files(str(tool_input.get("command") or ""))]
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
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": guard_bridge.blocked(*found, "Codex"),
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
