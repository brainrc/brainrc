"""GitHub Copilot (#307): the Copilot CLI and VS Code's Copilot agent read the same user folder,
~/.copilot ($COPILOT_HOME): skills, copilot-instructions.md, mcp-config.json and hooks/*.json.

brainrc's guard is its own hook file, hooks/brainrc.json, in the CLI's format: {"version": 1,
"hooks": {"preToolUse": [flat command entries]}}, which the merge already handles (as Cursor's).
"""
from __future__ import annotations

from .base import Adapter, server_entry


class Copilot(Adapter):
    name = "copilot"
    label = "GitHub Copilot (CLI, VS Code)"
    writes_mcp = True
    mcp_key = "mcpServers"

    def mcp_entry(self, server: dict) -> dict:
        kind = {"type": "http" if "url" in server else "stdio"}
        return kind | server_entry(server) | {"tools": ["*"]}
