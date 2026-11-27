"""OpenCode: agents rendered to its own format, MCP servers under "mcp", and opencode.jsonc read
beside opencode.json. Its guards are a plugin (harnesses.toml `plugin`), not a settings file."""
from __future__ import annotations

import json
import os
from pathlib import Path

from ..sources import frontmatter
from .base import Adapter

# OpenCode permission keys each Claude tool needs. An agent's missing tools become `deny`.
PERMISSIONS = {
    "Read": ("read", "list"), "Grep": ("grep",), "Glob": ("glob",), "Edit": ("edit",),
    "Write": ("edit",), "MultiEdit": ("edit",), "NotebookEdit": ("edit",), "Bash": ("bash",),
    "WebFetch": ("webfetch",), "WebSearch": ("websearch",), "Task": ("task",),
    "TodoWrite": ("todowrite",),
}


class OpenCode(Adapter):
    name = "opencode"
    label = "OpenCode"
    agents_format = "opencode"
    defines_agents_format = True
    writes_mcp = True
    mcp_key = "mcp"

    def render_agent(self, path: Path) -> str:
        """OpenCode rejects Claude's `tools: Read, Grep` string. Tools the agent lacks become `deny`;
        the rest are left to the user's own OpenCode permissions. `model` is dropped: a subagent
        then uses the model of the agent that called it."""
        text = path.read_text()
        head, _, body = text.partition("\n---\n")
        keep = [line for line in head.splitlines()[1:] if line.startswith(("name:", "description:"))]
        lines = ["---", *keep, "mode: subagent"]
        tools = frontmatter(path).get("tools")
        if tools is not None:
            allowed = {key for t in tools.split(",") for key in PERMISSIONS.get(t.strip(), ())}
            denied = sorted({k for keys in PERMISSIONS.values() for k in keys} - allowed)
            lines += ["permission:", *(f"  {key}: deny" for key in denied)]
        return "\n".join(lines) + "\n---\n" + body

    def copied_file(self, text: str, source: Path) -> str:
        """The guard plugin finds its guards from where it sits (a link resolves to the checkout or
        the package); a copy is told where its original is instead."""
        text = text.replace("realpathSync(fileURLToPath(import.meta.url))", json.dumps(os.path.realpath(source)))
        return super().copied_file(text, source)

    def mcp_entry(self, server: dict) -> dict:
        if "url" in server:
            return {"type": "remote", "url": server["url"], "enabled": True}
        env = server.get("env_from", [])
        entry = {"type": "local", "command": [server["command"], *server.get("args", [])]}
        return entry | ({"environment": {v: f"{{env:{v}}}" for v in env}} if env else {}) | {"enabled": True}

    def mcp_files(self, dest: Path) -> list[Path]:
        """OpenCode reads opencode.jsonc too, so it's a candidate beside an opencode.json."""
        return [dest, dest.with_suffix(".jsonc")] if dest.suffix == ".json" else [dest]
