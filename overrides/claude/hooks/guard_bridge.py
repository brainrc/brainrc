"""Runs core's guards for another harness's hook (Cursor, Codex, Antigravity, E11 #116; and E31's).

Each adapter turns its harness's event into Claude Code calls, (guard, tool name, tool input), and
asks decide() what the guards make of them where the command runs (cwd), which is what a pack's
[scope] needs. The guards stay the one evaluator, so every harness gets the same core rules, the
same pack [[guard.deny]] and [[guard.ask]] rules from $BRAINRC_HOME/guard-rules.json, and the same
unwrapping of `bash -c` and `$(...)`. A guard that can't run, or replies with something it can't
read, counts as no objection, as a broken Claude Code hook does.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTWARD, SECRETS = "guard_outward.py", "guard_secrets.py"


def objection(guard: str, tool: str, tool_input: dict, cwd: str | None) -> tuple[str, str] | None:
    """(decision, reason) when the guard asks or denies, else None."""
    payload = {"tool_name": tool, "tool_input": tool_input}
    if cwd:
        payload["cwd"] = cwd
    try:
        run = subprocess.run([sys.executable, str(HERE / guard)], input=json.dumps(payload),
                             capture_output=True, text=True, timeout=5)
        decision = json.loads(run.stdout).get("hookSpecificOutput", {}) if run.stdout.strip() else {}
    except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
        return None
    if run.returncode != 0 or not isinstance(decision, dict):
        return None
    if decision.get("permissionDecision") in ("ask", "deny"):
        return decision["permissionDecision"], str(decision.get("permissionDecisionReason")
                                                    or "brainrc's guard objected.")
    return None


def decide(calls: list[tuple[str, str, dict]], cwd: str | None) -> tuple[str, str] | None:
    """The strongest objection across calls: the first deny, else the first ask, else None."""
    ask = None
    for guard, tool, tool_input in calls:
        found = objection(guard, tool, tool_input, cwd)
        if found and found[0] == "deny":
            return found
        ask = ask or found
    return ask


def blocked(decision: str, reason: str, harness: str) -> str:
    """What the model and the user read when a harness that can't ask blocks the call instead."""
    if decision == "deny":
        return reason
    return (f"{reason} {harness} can't reliably ask for approval here, so this is blocked; "
            "ask the user to run it themselves.")


def shell_calls(command: str) -> list[tuple[str, str, dict]]:
    """A shell command, for both guards."""
    bash = {"command": command}
    return [(OUTWARD, "Bash", bash), (SECRETS, "Bash", bash)]


def read_call(path: str) -> list[tuple[str, str, dict]]:
    """Reading a file, for the secrets guard."""
    return [(SECRETS, "Read", {"file_path": path})] if path else []


def write_call(path: str, text: str) -> list[tuple[str, str, dict]]:
    """Writing text to a file, or into one, for the secrets guard."""
    return [(SECRETS, "Write", {"file_path": path, "content": text})] if path else []


def mcp_call(server: str, tool: str, tool_input: dict) -> list[tuple[str, str, dict]]:
    """An MCP tool, named as Claude Code names it (mcp__<server>__<tool>), for the outward guard."""
    return [(OUTWARD, f"mcp__{server}__{tool}", tool_input)] if server and tool else []
