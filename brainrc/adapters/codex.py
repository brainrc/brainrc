"""Codex: hooks in Claude Code's shape ($CODEX_HOME/hooks.json), and MCP servers as
`[mcp_servers.<name>]` tables in config.toml, inside a block marked as brainrc's."""
from __future__ import annotations

import json
import tomllib

from .base import Adapter

BLOCK_START = "# >>> brainrc mcp servers (written by brainrc apply; edits here are replaced)"
BLOCK_END = "# <<< brainrc mcp servers"
# The pre-rename markers: still recognized, so the next apply replaces an old block.
OLD_BLOCKS = [("# >>> ai-config mcp servers (written by aicfg apply; edits here are replaced)",
               "# <<< ai-config mcp servers")]


def _toml_str(value: str) -> str:
    return json.dumps(value)  # a JSON string with ASCII escapes is a valid TOML basic string


def _toml_list(values: list[str]) -> str:
    return "[" + ", ".join(map(_toml_str, values)) + "]"


def render_block(servers: dict[str, dict]) -> str:
    """The servers as Codex `[mcp_servers.<name>]` tables (env vars forwarded by name)."""
    tables = []
    for name, s in servers.items():
        lines = [f"[mcp_servers.{name}]"]
        if "url" in s:
            lines.append(f"url = {_toml_str(s['url'])}")
        else:
            lines.append(f"command = {_toml_str(s['command'])}")
            if s.get("args"):
                lines.append(f"args = {_toml_list(s['args'])}")
            if s.get("env_from"):
                lines.append(f"env_vars = {_toml_list(s['env_from'])}")
        tables.append("\n".join(lines))
    return "\n\n".join(tables) + "\n" if tables else ""


def blocks(text: str) -> list[tuple[int, int]]:
    """(start, end) offsets of each complete brainrc block, old markers included, end after its newline."""
    spans, pos = [], 0
    while True:
        found = [(text.find(o, pos), o, c) for o, c in [(BLOCK_START, BLOCK_END), *OLD_BLOCKS]]
        found = [f for f in found if f[0] != -1]
        if not found:
            return spans
        start, open_, close = min(found)
        end = text.find(close, start + len(open_))
        if end == -1:
            return spans
        end += len(close)
        spans.append((start, end + 1 if text[end:end + 1] == "\n" else end))
        pos = spans[-1][1]


def _drop(text: str, start: int, end: int) -> str:
    """Remove text[start:end] and one blank line beside it, so removing a block leaves no gap."""
    if text[end:end + 1] == "\n":
        end += 1
    elif start and text[start - 1] == "\n" and (start == 1 or text[start - 2] == "\n"):
        start -= 1
    return text[:start] + text[end:]


class Codex(Adapter):
    name = "codex"
    label = "Codex"
    writes_mcp = True
    records_mcp = False  # the marked block is the record

    def mcp_text_change(self, text: str, servers: dict[str, dict]) -> tuple[str, list[str], list[str]]:
        spans = blocks(text)
        rest = text
        for start, end in reversed(spans):
            rest = rest[:start] + rest[end:]
        foreign = tomllib.loads(rest).get("mcp_servers", {})
        conflicts = sorted(n for n in servers if n in foreign)
        block = render_block({n: s for n, s in servers.items() if n not in conflicts})
        new = f"{BLOCK_START}\n{block}{BLOCK_END}\n" if block else ""
        if not spans:
            out = (text.rstrip("\n") + "\n\n" if text.strip() else "") + new if new else text
        else:
            # The first block is replaced where it is, so the user's bytes around it never move.
            out = text
            for start, end in reversed(spans[1:]):
                out = _drop(out, start, end)
            start, end = spans[0]
            out = out[:start] + new + out[end:] if new else _drop(out, start, end)
        owned = [n for n in servers if n not in conflicts]
        return out, conflicts, owned
