"""The adapter interface (#306): what brainrc knows about one AI tool beyond its paths.

harnesses.toml says where a tool reads each kind of content. An Adapter says what that content has
to look like there: how agents are written, where the settings file keeps hooks, how MCP servers
are spelled, which guard rules a sandbox can take, and the tool's name in prose. The defaults
below describe a tool that reads everything as Claude Code writes it, so an adapter overrides only
what its tool does differently.

A tool brainrc doesn't ship can come from a Python package: one entry point in the
`brainrc.adapters` group whose object is an Adapter subclass (or instance) that also sets `paths`,
its harnesses.toml table (docs/adapters.md).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# How a Python hook finds itself; through a link it resolves to the source, so a copy is told that path.
PY_SELF = "Path(__file__).resolve()"


class Adapter:
    # The harnesses.toml table this adapter serves, e.g. "codex".
    name: str = ""
    # The tool's name in prose and in the capability matrix, e.g. "Codex".
    label: str = ""
    # Default harnesses.toml table, for a tool core's harnesses.toml doesn't list (an adapter from a
    # package). Shipped tools keep their paths in harnesses.toml; harnesses.local.toml overrides both.
    paths: dict[str, str | bool] = {}

    # The agent and settings formats this tool uses unless its table sets `agents_format` or
    # `settings_format`. A format is named after the adapter that defines it; "claude" is the base.
    agents_format: str = "claude"
    settings_format: str = "claude"
    # True when this adapter defines a format of that kind (render_agent, or hooks_view/hooks_put).
    defines_agents_format: bool = False
    defines_settings_format: bool = False

    # MCP: True when apply can write this tool's MCP servers. JSON tools name the key the servers
    # sit under (mcp_key) and spell one server (mcp_entry); others override mcp_text_change.
    writes_mcp: bool = False
    mcp_key: str | None = None
    records_mcp: bool = True  # False when the file itself marks what is brainrc's (Codex's block)

    # Guard rules a tool's OS sandbox can take (#322): rule kind -> [(section, key)] lists in its
    # settings file, e.g. {"path": [("filesystem", "denyRead")]}. Empty: no sandbox brainrc writes.
    sandbox: dict[str, list[tuple[str, str]]] = {}

    # True when its hook entries give `timeout` in milliseconds (Gemini CLI), not seconds.
    hook_timeout_ms: bool = False

    # --- agents -------------------------------------------------------------------------------
    def render_agent(self, path: Path) -> str:
        """An agent file rewritten in this adapter's agent format (defines_agents_format only)."""
        raise NotImplementedError(f"{self.name} defines no agent format")

    # --- settings and hooks -------------------------------------------------------------------
    def hooks_view(self, current: dict) -> dict:
        """The settings file in Claude Code's shape (hooks under "hooks"), whatever its own format."""
        return current

    def hooks_put(self, current: dict, merged: dict) -> dict:
        """current with the hooks in merged (Claude Code's shape) put back in this format's place."""
        return merged

    def hooks_problem(self, current: dict) -> str | None:
        """Why this format can't merge into current (a JSON object), or None when it can."""
        return None

    # --- Windows hooks (#178) --------------------------------------------------------------------
    # The shell the tool runs a hook command in on Windows, as its docs say: "powershell", "cmd",
    # or None where they don't say (the line then holds nothing any of them reads differently).
    windows_shell: str | None = None

    def windows_hook(self, hook: dict, exe: str, args: list[str], source: str) -> dict:
        """One of brainrc's hooks on Windows: the Python call (brainrc/hookcmd.py) in place of the
        POSIX line. An adapter whose tool takes a Windows-only field writes it there instead."""
        from .. import hookcmd
        return hook | {"command": hookcmd.line(exe, args, source, self.windows_shell)}

    # --- copy mode (#177) ------------------------------------------------------------------------
    def copied_file(self, text: str, source: Path) -> str:
        """A file apply copies into this tool where it can't link (Windows without Developer Mode),
        rewritten so it behaves as the link would. A Python hook that finds the guards beside its
        own real path (`Path(__file__).resolve()`) is given its source's real path instead."""
        if source.suffix == ".py" and PY_SELF in text:
            return text.replace(PY_SELF, f"Path({json.dumps(os.path.realpath(source))})")
        return text

    # --- MCP ----------------------------------------------------------------------------------
    def mcp_entry(self, server: dict) -> dict:
        """One server from mcp/servers.toml as this tool's JSON config spells it."""
        raise NotImplementedError(f"{self.name} writes no MCP servers")

    def mcp_files(self, dest: Path) -> list[Path]:
        """The files that may hold this tool's MCP servers, its `mcp` path first."""
        return [dest]

    def mcp_text_change(self, text: str, servers: dict[str, dict]) -> tuple[str, list[str], list[str]] | None:
        """(new text, conflicting names, owned names) for a file that isn't JSON at mcp_key, or None
        to use the JSON merge."""
        return None

    def __repr__(self) -> str:
        return f"<adapter {self.name}>"


def server_entry(server: dict, env_ref: str | None = "${{{}}}", url: dict | None = None,
                 stdio: dict | None = None) -> dict:
    """The common MCP spelling: {"url"} for a remote server, {"command", "args", "env"} for a local
    one. env_ref spells a reference to the variable that `env_from` names ("${{{}}}" -> "${VAR}");
    None leaves `env` out, for a tool that passes its own environment on and reads no reference.
    url and stdio add a tool's own keys to each kind."""
    if "url" in server:
        return {"url": server["url"]} | (url or {})
    entry = {"command": server["command"], "args": list(server.get("args", []))}
    env = server.get("env_from", [])
    if env and env_ref is not None:
        entry["env"] = {v: env_ref.format(v) for v in env}
    return entry | (stdio or {})


class Plain(Adapter):
    """A harness with no adapter of its own (a table the user added in harnesses.local.toml): it
    reads content as Claude Code writes it, and gets no MCP servers or sandbox."""

    def __init__(self, name: str):
        self.name = name
        self.label = name
