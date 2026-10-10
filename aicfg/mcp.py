"""MCP servers: each source's mcp/servers.toml, merged into every harness's MCP config.

Formats were checked with the real CLIs (Claude Code 2.1.296, Codex 0.161.0, OpenCode 1.18.35).
Environment variables are written only as references the harness expands at launch, never as
values. A server the user defined under the same name is left alone and reported.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import BACKUPS_KEPT, ConfigError, aicfg_home, expand, load_harnesses
from .sources import Source

REGISTRY = Path("mcp") / "servers.toml"
SERVER_KEYS = {"command", "args", "url", "env_from", "harnesses"}
NAME = re.compile(r"^[A-Za-z0-9_-]+$")
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# The harnesses aicfg can write MCP servers for, and the key their JSON config keeps them under.
ADAPTERS = {"claude": "mcpServers", "codex": None, "opencode": "mcp"}
BLOCK_START = "# >>> ai-config mcp servers (written by aicfg apply; edits here are replaced)"
BLOCK_END = "# <<< ai-config mcp servers"


def _registry(src: Source) -> dict:
    path = src.root / REGISTRY
    if not path.is_file():
        return {}
    try:
        servers = tomllib.loads(path.read_text()).get("servers", {})
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{src.rel(path)}: invalid TOML ({e})") from None
    return servers if isinstance(servers, dict) else {}


def check_servers(srcs: list[Source]) -> list[str]:
    """Every problem with the sources' MCP registries, for validate (and before apply writes)."""
    errors, seen = [], {}
    names = set(load_harnesses(include_disabled=True))
    for src in srcs:
        try:
            servers = _registry(src)
        except ConfigError as e:
            errors.append(str(e))
            continue
        where = src.rel(src.root / REGISTRY)
        for name, s in servers.items():
            bad = lambda why: errors.append(f"{where}: server `{name}`: {why}")  # noqa: E731
            if not NAME.match(name):
                bad("names may use letters, digits, `-` and `_` only")
            if not src.is_core and not name.startswith(src.prefix):
                bad(f"must start with the pack prefix `{src.prefix}`")
            if name in seen:
                bad(f"also defined in {seen[name]}")
            seen.setdefault(name, where)
            if not isinstance(s, dict):
                bad("must be a table")
                continue
            if "env" in s:
                bad("`env` would put values in config files; name the variables in `env_from` instead")
            for key in sorted(set(s) - SERVER_KEYS - {"env"}):
                bad(f"unknown key `{key}`")
            if ("command" in s) == ("url" in s):
                bad("needs exactly one of `command` (stdio) or `url` (HTTP)")
            if "url" in s and "args" in s:
                bad("`args` only applies to a `command`")
            for key in ("command", "url"):
                if key in s and not isinstance(s[key], str):
                    bad(f"`{key}` must be a string")
            for key in ("args", "env_from", "harnesses"):
                if key in s and not (isinstance(s[key], list) and all(isinstance(v, str) for v in s[key])):
                    bad(f"`{key}` must be a list of strings")
            if "url" in s and s.get("env_from"):
                bad("`env_from` only applies to a `command`")
            for var in s.get("env_from", []) if isinstance(s.get("env_from"), list) else []:
                if isinstance(var, str) and not ENV_NAME.match(var):
                    bad(f"`{var}` in `env_from` isn't an environment variable name")
            for h in s.get("harnesses", []) if isinstance(s.get("harnesses"), list) else []:
                if h not in names:
                    bad(f"unknown harness `{h}` in `harnesses`")
    for name, h in load_harnesses(include_disabled=True).items():
        if "mcp" in h and name not in ADAPTERS:
            errors.append(f"harnesses.toml [{name}] sets `mcp`, but aicfg can only write MCP servers "
                          f"for {', '.join(ADAPTERS)}")
    return errors


def load_servers(srcs: list[Source]) -> dict[str, dict]:
    """Every source's servers by name, core first. Call check_servers first."""
    servers: dict[str, dict] = {}
    for src in srcs:
        for name, s in _registry(src).items():
            servers.setdefault(name, s)
    return servers


def render_entry(harness: str, s: dict) -> dict:
    """One server as Claude Code's or OpenCode's JSON config wants it."""
    env = s.get("env_from", [])
    if harness == "claude":
        if "url" in s:
            return {"type": "http", "url": s["url"]}
        entry = {"type": "stdio", "command": s["command"], "args": list(s.get("args", []))}
        return entry | ({"env": {v: f"${{{v}}}" for v in env}} if env else {})
    if "url" in s:
        return {"type": "remote", "url": s["url"], "enabled": True}
    entry = {"type": "local", "command": [s["command"], *s.get("args", [])]}
    return entry | ({"environment": {v: f"{{env:{v}}}" for v in env}} if env else {}) | {"enabled": True}


def _toml_str(value: str) -> str:
    return json.dumps(value)  # a JSON string with ASCII escapes is a valid TOML basic string


def _toml_list(values: list[str]) -> str:
    return "[" + ", ".join(map(_toml_str, values)) + "]"


def render_codex_block(servers: dict[str, dict]) -> str:
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


@dataclass
class McpSync:
    harness: str
    dest: Path
    servers: dict[str, dict]  # what this harness should have; empty when it's disabled


def mcp_plan(srcs: list[Source]) -> list[McpSync]:
    """One sync per harness with an `mcp` file; disabled harnesses get none, so theirs are removed."""
    servers = load_servers(srcs)
    enabled = load_harnesses()
    syncs = []
    for name, h in load_harnesses(include_disabled=True).items():
        if "mcp" not in h or name not in ADAPTERS:
            continue
        wanted = {n: s for n, s in servers.items()
                  if name in enabled and name in s.get("harnesses", [name])}
        syncs.append(McpSync(name, expand(h["mcp"]), wanted))
    return syncs


def _owned_file() -> Path:
    return aicfg_home() / "mcp-owned.json"


def _owned() -> dict[str, list[str]]:
    try:
        data = json.loads(_owned_file().read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _strip_block(text: str) -> tuple[str, str]:
    """(text without ai-config's block, the block's body)."""
    start, end = text.find(BLOCK_START), text.find(BLOCK_END)
    if start == -1 or end < start:
        return text, ""
    before, body, after = text[:start], text[start + len(BLOCK_START):end], text[end + len(BLOCK_END):]
    return before.rstrip("\n") + ("\n" if before.strip() else "") + after.lstrip("\n"), body


def _codex_change(m: McpSync, text: str) -> tuple[str, list[str], list[str]]:
    rest, _ = _strip_block(text)
    foreign = tomllib.loads(rest).get("mcp_servers", {})
    conflicts = sorted(n for n in m.servers if n in foreign)
    block = render_codex_block({n: s for n, s in m.servers.items() if n not in conflicts})
    if block:
        rest = (rest.rstrip("\n") + "\n\n" if rest.strip() else "") + f"{BLOCK_START}\n{block}{BLOCK_END}\n"
    owned = [n for n in m.servers if n not in conflicts]
    return rest, conflicts, owned


def _json_change(m: McpSync, text: str) -> tuple[str, list[str], list[str]]:
    data = json.loads(text) if text.strip() else {}
    if not isinstance(data, dict):
        raise ValueError("not a JSON object")
    key = ADAPTERS[m.harness]
    current = data.get(key) if isinstance(data.get(key), dict) else {}
    was_owned = set(_owned().get(str(m.dest), []))
    servers = {n: e for n, e in current.items() if n not in was_owned or n in m.servers}
    conflicts, owned = [], []
    for name, s in m.servers.items():
        entry = render_entry(m.harness, s)
        if name in current and name not in was_owned and current[name] != entry:
            conflicts.append(name)  # the user's own server: never overwritten
            continue
        servers[name] = entry
        owned.append(name)
    if servers == current or (not servers and key not in data):
        return text, conflicts, owned
    new = dict(data)
    if servers:
        new[key] = servers
    else:
        new.pop(key, None)
    return json.dumps(new, indent=2) + "\n", conflicts, owned


def mcp_change(m: McpSync) -> tuple[str, str | None, list[str], list[str]]:
    """(state, new text, conflicting names, names ai-config owns afterwards).
    state is ok | merge | invalid (the file can't be parsed, so it's left alone)."""
    text = m.dest.read_text() if m.dest.is_file() else ""
    try:
        new, conflicts, owned = (_codex_change if m.harness == "codex" else _json_change)(m, text)
    except (ValueError, tomllib.TOMLDecodeError):
        return "invalid", None, [], []
    return ("ok" if new == text else "merge"), new, conflicts, owned


def write_mcp(m: McpSync, text: str, owned: list[str]) -> None:
    """Back up, then replace atomically, as for settings files; record what ai-config owns."""
    m.dest.parent.mkdir(parents=True, exist_ok=True)
    if m.dest.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(m.dest, m.dest.with_name(f"{m.dest.name}.bak-aicfg-{stamp}"))
        for old in sorted(m.dest.parent.glob(f"{m.dest.name}.bak-aicfg-*"))[:-BACKUPS_KEPT]:
            old.unlink()
    tmp = m.dest.with_name(f".{m.dest.name}.aicfg-tmp")
    tmp.write_text(text)
    os.replace(tmp, m.dest)
    record_owned(m, owned)


def record_owned(m: McpSync, owned: list[str]) -> None:
    if m.harness == "codex":
        return  # the marked block is the record
    data = _owned()
    if owned:
        data[str(m.dest)] = sorted(owned)
    else:
        data.pop(str(m.dest), None)
    if data or _owned_file().exists():
        _owned_file().parent.mkdir(parents=True, exist_ok=True)
        _owned_file().write_text(json.dumps(data, indent=2) + "\n")

