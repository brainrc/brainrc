"""MCP servers: each source's mcp/servers.toml, merged into every harness's MCP config.

Formats were checked with the real CLIs (Claude Code 2.1.296, Codex 0.161.0, OpenCode 1.18.35).
Environment variables are written only as references the harness expands at launch, never as
values. A server the user defined under the same name is left alone and reported.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import adapters, jsonc
from .config import ConfigError, expand, former_homes, in_scope, installs, load_harnesses, settings_home
from .settings import replace_file
from .sources import Source
from .adapters.codex import render_block as render_codex_block  # noqa: F401  (tests and callers)

REGISTRY = Path("mcp") / "servers.toml"
SERVER_KEYS = {"command", "args", "url", "env_from", "harnesses"}
NAME = re.compile(r"^[A-Za-z0-9_-]+$")
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def writers() -> list[str]:
    """The harnesses brainrc can write MCP servers for: those whose adapter writes them (#306)."""
    return [n for n, a in adapters.every().items() if a.writes_mcp]


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
        if "mcp" in h and not adapters.get(name).writes_mcp:
            errors.append(f"harnesses.toml [{name}] sets `mcp`, but brainrc can only write MCP servers "
                          f"for {', '.join(writers())}")
    return errors


def load_servers(srcs: list[Source]) -> dict[str, dict]:
    """Every source's servers by name, core first. Call check_servers first."""
    servers: dict[str, dict] = {}
    for src in srcs:
        for name, s in _registry(src).items():
            servers.setdefault(name, s)
    return servers


def render_entry(harness: str, s: dict) -> dict:
    """One server as harness's JSON config wants it (its adapter's mcp_entry)."""
    return adapters.get(harness).mcp_entry(s)


@dataclass
class McpSync:
    harness: str
    dest: Path
    servers: dict[str, dict]  # what this harness should have; empty when it's disabled


def mcp_plan(srcs: list[Source]) -> list[McpSync]:
    """One sync per harness with an `mcp` file; disabled harnesses get none, so theirs are removed."""
    servers = load_servers(srcs) if installs("mcp") else {}  # none unless the profile installs them
    enabled = load_harnesses()
    syncs = []
    for name, h in load_harnesses(include_disabled=True).items():
        if "mcp" not in h or not adapters.get(name).writes_mcp or not in_scope(name):
            continue
        wanted = {n: s for n, s in servers.items()
                  if name in enabled and name in s.get("harnesses", [name])}
        syncs.append(McpSync(name, mcp_file(name, h), wanted))
    return syncs


def mcp_files(name: str, h: dict) -> list[Path]:
    """The files that may hold the harness's MCP servers: its `mcp` path, and any other its adapter
    names (OpenCode reads an opencode.jsonc beside opencode.json)."""
    return adapters.get(name).mcp_files(expand(h["mcp"]))


def mcp_file(name: str, h: dict) -> Path:
    """The MCP file apply writes: its `mcp` path, except OpenCode's opencode.jsonc when only that
    exists, or when brainrc's servers are there and not in opencode.json."""
    files = mcp_files(name, h)
    if len(files) == 1 or not files[1].is_file():
        return files[0]
    owned = _owned()
    if not files[0].exists() or (owned.get(str(files[1])) and not owned.get(str(files[0]))):
        return files[1]
    return files[0]


def _owned_file() -> Path:
    return settings_home() / "mcp-owned.json"


def _read_record(path: Path) -> dict[str, list[str]]:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _owned() -> dict[str, list[str]]:
    """Former homes' records (read-only), overlaid per file by the resolved home's, which wins."""
    merged: dict[str, list[str]] = {}
    for path in [*(h / "mcp-owned.json" for h in former_homes()), _owned_file()]:
        for dest, names in _read_record(path).items():
            if isinstance(names, list):
                merged[dest] = sorted({n for n in names if isinstance(n, str)})
    return merged


def _json_change(m: McpSync, text: str) -> tuple[str, list[str], list[str]]:
    commented = m.dest.suffix == ".jsonc"
    data = (jsonc.loads if commented else json.loads)(text) if text.strip() else {}
    if not isinstance(data, dict):
        raise ValueError("not a JSON object")
    key = adapters.get(m.harness).mcp_key
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
    if commented and text.strip():  # edit in place, so the user's comments stay
        out = _jsonc_edit(text, key, data.get(key), servers)
        if jsonc.loads(out) not in (new, {**new, key: {}}):
            raise ValueError("the in-place edit didn't round-trip")
        return out, conflicts, owned
    return json.dumps(new, indent=2) + "\n", conflicts, owned


def _jsonc_edit(text: str, key: str, current, servers: dict) -> str:
    """text with its `key` object holding servers: one server at a time, so the user's servers and
    the comments on them are never rewritten. An emptied object goes, unless comments are in it."""
    if not isinstance(current, dict):
        return jsonc.set_key(text, key, servers or None)
    for name in sorted(set(current) | set(servers)):
        if current.get(name) != servers.get(name):
            text = jsonc.set_key(text, (key, name), servers.get(name))
    if not servers:
        try:
            text = jsonc.set_key(text, key, None, strict=True)
        except ValueError:
            pass  # a comment inside it: keep `"mcp": {}` with the comment
    return text


def mcp_change(m: McpSync) -> tuple[str, str | None, list[str], list[str]]:
    """(state, new text, conflicting names, names brainrc owns afterwards).
    state is ok | merge | invalid (the file can't be parsed, so it's left alone)."""
    text = m.dest.read_text() if m.dest.is_file() else ""
    try:
        custom = adapters.get(m.harness).mcp_text_change(text, m.servers)
        new, conflicts, owned = custom if custom is not None else _json_change(m, text)
    except (ValueError, IndexError, tomllib.TOMLDecodeError):
        return "invalid", None, [], []
    return ("ok" if new == text else "merge"), new, conflicts, owned


def write_mcp(m: McpSync, text: str, owned: list[str], before: str | None) -> None:
    """Back up, then replace atomically, as for settings files; record what brainrc owns."""
    replace_file(m.dest, text, before)
    record_owned(m, owned)


def record_owned(m: McpSync, owned: list[str]) -> None:
    if not adapters.get(m.harness).records_mcp:
        return  # the file marks what is brainrc's (Codex's block)
    data = _read_record(_owned_file())  # only the resolved home's own record is ever written
    dest = str(m.dest)
    if owned:
        data[dest] = sorted(owned)
    elif any(isinstance(_read_record(h / "mcp-owned.json").get(dest), list) for h in former_homes()):
        data[dest] = []  # shadows a former record, so it can't claim a server added later
    else:
        data.pop(dest, None)
    if data or _owned_file().exists():
        _owned_file().parent.mkdir(parents=True, exist_ok=True)
        _owned_file().write_text(json.dumps(data, indent=2) + "\n")

