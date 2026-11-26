"""Devin Local (#309), the agent in Devin Desktop, which is what Windsurf became: Windsurf's docs
now lead to Devin's, and Devin Desktop no longer starts Cascade conversations. It reads
~/.config/devin (skills, AGENTS.md, mcp_config.json, and hooks under "hooks" in config.json, in
Claude Code's shape with its own tool names).
"""
from __future__ import annotations

from .base import Adapter, server_entry


class Devin(Adapter):
    name = "devin"
    label = "Devin Local (was Windsurf)"
    writes_mcp = True
    mcp_key = "mcpServers"

    def mcp_entry(self, server: dict) -> dict:
        # Devin's docs spell a variable ${env:VAR}; `transport` says which remote protocol.
        return server_entry(server, "${{env:{}}}", url={"transport": "http"})
