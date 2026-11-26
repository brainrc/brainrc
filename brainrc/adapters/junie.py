"""JetBrains Junie (#312): skills, agents, AGENTS.md, MCP servers and a PreToolUse guard in
~/.junie. Its subagents take Claude Code's frontmatter and its hooks Claude Code's shape, under
"hooks" in ~/.junie/config.json. Its MCP config reads no variable references, so a server's
`env_from` variables come from the environment Junie runs in.
"""
from __future__ import annotations

from .base import Adapter, server_entry


class Junie(Adapter):
    name = "junie"
    label = "JetBrains Junie"
    writes_mcp = True
    mcp_key = "mcpServers"
    # "Executed via `sh -c` on macOS/Linux and `cmd /c` on Windows"
    # (https://junie.jetbrains.com/docs/junie-cli-hooks.html).
    windows_shell = "cmd"

    def mcp_entry(self, server: dict) -> dict:
        return server_entry(server, None)
