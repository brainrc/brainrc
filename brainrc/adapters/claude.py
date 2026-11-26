"""Claude Code: the base format every other adapter starts from."""
from __future__ import annotations

from .base import Adapter


class Claude(Adapter):
    name = "claude"
    label = "Claude Code"
    writes_mcp = True
    mcp_key = "mcpServers"
    # Packs' path and host guard rules compile into its sandbox settings (#322).
    sandbox = {"path": [("filesystem", "denyRead"), ("filesystem", "denyWrite")],
               "host": [("network", "deniedDomains")]}

    def windows_hook(self, hook: dict, exe: str, args: list[str], source: str) -> dict:
        # Exec form, no shell: "command" a real executable and "args" its arguments
        # (https://code.claude.com/docs/en/hooks). Shell form there is Git Bash, else PowerShell.
        return {k: v for k, v in hook.items() if k not in ("command", "shell")} | {
            "command": exe, "args": [*args, "-c", source]}

    def mcp_entry(self, server: dict) -> dict:
        if "url" in server:
            return {"type": "http", "url": server["url"]}
        env = server.get("env_from", [])
        entry = {"type": "stdio", "command": server["command"], "args": list(server.get("args", []))}
        return entry | ({"env": {v: f"${{{v}}}" for v in env}} if env else {})
