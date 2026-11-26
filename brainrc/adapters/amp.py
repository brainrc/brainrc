"""Amp (#311): skills, AGENTS.md and MCP servers in ~/.config/amp. Its settings keys carry an
`amp.` prefix, so servers sit under "amp.mcpServers" in settings.json (settings.jsonc read too).
Amp has no command hooks: its only hook point is a TypeScript plugin API, which brainrc doesn't
write yet, so it gets no guard.
"""
from __future__ import annotations

from pathlib import Path

from .base import Adapter, server_entry


class Amp(Adapter):
    name = "amp"
    label = "Amp"
    writes_mcp = True
    mcp_key = "amp.mcpServers"

    def mcp_entry(self, server: dict) -> dict:
        return server_entry(server)

    def mcp_files(self, dest: Path) -> list[Path]:
        return [dest, dest.with_suffix(".jsonc")] if dest.suffix == ".json" else [dest]
