#!/usr/bin/env python3
"""Claude Code PreToolUse hook for Bash: ask before Proxmox guest and Talos node changes.

Reads the hook payload (JSON) on stdin. Prints a PreToolUse decision of "ask" for `qm`/`pct`
destroy/stop/... and `talosctl` upgrade/reset/...; everything else gets no output. The rules
match the raw command text, so commands inside `sh -c '...'` or after `;` are caught too.
"""
from __future__ import annotations

import json
import re
import sys

# Up to the end of the current simple command (don't match across ; && || |).
SAME_CMD = r"[^|;&\n]*"

RULES: list[tuple[str, str]] = [
    (r"\b(qm|pct)\s+(destroy|stop|shutdown|reboot|reset|rollback|migrate)\b", "changes Proxmox guests"),
    (r"\btalosctl\b" + SAME_CMD + r"\b(apply-config|upgrade|upgrade-k8s|reset|reboot|shutdown|bootstrap)\b",
     "changes Talos nodes"),
]


def reason_for(command: str) -> str | None:
    for pattern, reason in RULES:
        if re.search(pattern, command):
            return reason
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:  # bad JSON or non-UTF-8 input
        return 0  # malformed payload: defer to the harness's normal permission flow
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input")
    reason = reason_for(str(tool_input.get("command", ""))) if isinstance(tool_input, dict) else None
    if reason:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"brainrc homelab guard: {reason}. Confirm this is approved.",
            }
        }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
