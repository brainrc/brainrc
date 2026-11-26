"""Gemini CLI (#308): skills, GEMINI.md, MCP servers and a BeforeTool guard, all in ~/.gemini.

Google ended Gemini CLI for individual accounts on June 18, 2026, in favour of Antigravity CLI;
it goes on for Gemini Code Assist Standard and Enterprise and for paid API keys. It shares ~/.gemini
with Antigravity, so harnesses.toml keeps it off by default: `[gemini] enabled = true` in
harnesses.local.toml turns it on. Its settings.json holds both the hooks and the MCP servers.
"""
from __future__ import annotations

from .base import Adapter, server_entry


class Gemini(Adapter):
    name = "gemini"
    label = "Gemini CLI"
    writes_mcp = True
    mcp_key = "mcpServers"
    hook_timeout_ms = True

    def mcp_entry(self, server: dict) -> dict:
        if "url" in server:  # httpUrl is streamable HTTP; `url` would mean SSE
            return {"httpUrl": server["url"]}
        return server_entry(server)
