#!/usr/bin/env python3
"""Claude Code PreToolUse hook for Read/Write/Edit/MultiEdit: keep secrets out of files and context.

- Writing or editing content that looks like a credential → deny.
- Writing or editing a .env file → deny (example/sample/template files are allowed).
- Reading a .env file → ask.
Matched secret values are never echoed back; only the pattern name is reported.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import PurePath

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key id", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI-style API key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9_-]{32,}")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Stripe live key", re.compile(r"\b[rs]k_live_[0-9A-Za-z]{24,}\b")),
    ("private key", re.compile("-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")),
]

ENV_OK_SUFFIXES = (".example", ".sample", ".template", ".dist")


def is_env_file(path: str) -> bool:
    name = PurePath(path).name
    return (name == ".env" or name.startswith(".env.")) and not name.endswith(ENV_OK_SUFFIXES)


def written_text(tool: str, tool_input: dict) -> str:
    if tool == "Write":
        return str(tool_input.get("content", ""))
    if tool == "Edit":
        return str(tool_input.get("new_string", ""))
    if tool == "MultiEdit":
        return "\n".join(str(e.get("new_string", "")) for e in tool_input.get("edits", []))
    return ""


def decide(tool: str, tool_input: dict) -> tuple[str, str] | None:
    path = str(tool_input.get("file_path", ""))
    if tool == "Read":
        if is_env_file(path):
            return "ask", "reading an env file may expose secrets"
        return None
    if tool not in ("Write", "Edit", "MultiEdit"):
        return None
    if is_env_file(path):
        return "deny", "writing .env files is blocked; use an .env.example with placeholder values"
    text = written_text(tool, tool_input)
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return "deny", f"content looks like a {name}; reference it via an environment variable instead"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    result = decide(str(payload.get("tool_name", "")), payload.get("tool_input", {}) or {})
    if result:
        decision, reason = result
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": f"ai-config guard: {reason}.",
            }
        }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
