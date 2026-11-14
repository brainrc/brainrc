"""`brainrc audit` (#291): one list of what the agents load. Every skill, agent, command, rule, hook
and MCP server brainrc puts into each harness (tool), with the source it came from, that source's
commit and the item's hash, plus each pack's permissions from brainrc.lock and the MCP tool pins.

It reads only: no network, nothing written. Paths under ~ are written with ~, a URL loses any user
name or password, and an MCP server's environment is named, never read.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import config, lock, mcp_pins
from .config import ConfigError, load_harnesses, tilde
from .mcp import _registry, check_servers, mcp_plan
from .packs import head
from .plan import Link, plan, render_fragment
from .sources import Source, core_version, item_name, markdown_files, sources, tree_files

KIND = {"skills": "skill", "agents": "agent", "commands": "command"}
ORDER = ("skill", "agent", "command", "rule", "hook", "mcp")
SCRIPT = re.compile(r"\{\{hooks_dir\}\}/([^\"'\s]+)")


def _hash(path: Path) -> str:
    """A file's sha256, or a directory's: the sha256 of each file's path and hash, one per line."""
    if path.is_dir():
        lines = "".join(f"{rel} {lock.digest(f.read_bytes())}\n" for rel, f in tree_files(path))
        return lock.digest(lines.encode())
    return lock.digest(path.read_bytes())


def _origins(srcs: list[Source], locked: dict) -> dict[str, dict]:
    """Each source's provenance: core's version (and commit in a checkout), a git pack's url, ref
    and the commit it has checked out, a path pack's path; with the lock's permissions."""
    layered = config._layered("packs")
    out = {}
    for src in srcs:
        if src.is_core:
            commit = head(src.root) if (src.root / ".git").exists() else None
            out["core"] = {"version": ".".join(map(str, core_version())), **({"commit": commit} if commit else {})}
            continue
        cfg = layered.get(src.key, {})
        entry = {"git": lock.clean_url(str(cfg["git"])), "ref": str(cfg.get("ref", "HEAD")),
                 "commit": head(src.root)} if "git" in cfg else {"path": lock.shown_path(str(cfg.get("path", src.root)))}
        perms = (locked.get("packs", {}).get(src.key) or {}).get("permissions")
        out[src.key] = entry | ({"permissions": perms} if perms is not None else {})
    return out


def _owner(path: Path, srcs: list[Source]) -> Source | None:
    for src in sorted(srcs, key=lambda s: len(s.root.parts), reverse=True):  # a pack inside core's checkout
        if path == src.root or src.root in path.parents:
            return src
    return None


def _items(harness: str, links: list[Link], srcs: list[Source], roots: list[Path]) -> list[dict]:
    found = []
    agents = {p.name: (src, p) for src in srcs for p in markdown_files("agents", src)}
    for link in links:
        if link.harness != harness or link.copy or link.source.name == "hooks":
            continue  # the hooks dir: its hooks are listed from the settings fragments
        installed = link.state(roots) == "ok"
        if link.source == config.rendered_instructions():
            found += _rules(srcs, installed, tilde(link.dest))
            continue
        if link.source.parent == config.rendered_agents_dir() and link.source.name in agents:
            src, path = agents[link.source.name]
            kind = "agent"
        elif link.source.name == "plugin.js":
            src, path, kind = _owner(link.source, srcs), link.source, "hook"
        else:
            src, path = _owner(link.source, srcs), link.source
            kind = KIND.get(path.parent.name)
        if src is None or kind is None or not path.exists():
            continue
        found.append({"kind": kind, "name": item_name(path) if kind != "hook" else path.name,
                      "source": src.key or src.name, "file": src.rel(path), "hash": _hash(path),
                      "path": tilde(link.dest), "installed": installed})
    return found


def _rules(srcs: list[Source], installed: bool, dest: str) -> list[dict]:
    """Every rule in the instructions file the harness loads, as render_instructions joins them."""
    found, local = [], []
    for src in srcs:
        for p in markdown_files("rules", src):
            found.append({"kind": "rule", "name": p.stem, "source": src.key or src.name, "file": src.rel(p),
                          "hash": _hash(p), "path": dest, "installed": installed})
        rules_dir = (config.local_dir() if src.is_core else src.root) / "rules"
        local += sorted(rules_dir.glob("*.local.md")) if rules_dir.is_dir() else []
    found += [{"kind": "rule", "name": p.stem, "source": "local", "file": tilde(p), "hash": _hash(p),
               "path": dest, "installed": installed} for p in local]
    return found


def _hooks(harness: str, merges, srcs: list[Source]) -> list[dict]:
    """Each hook command the settings fragments merge into the harness's settings file."""
    found = []
    for merge in merges:
        if merge.harness != harness:
            continue
        try:
            current = merge.dest.read_text(encoding="utf-8")
        except OSError:
            current = ""
        for fragment, hooks_dir in merge.fragments:
            src = _owner(fragment, srcs)
            if src is None:
                continue
            try:
                rendered = render_fragment(fragment, hooks_dir)
                raw = json.loads(fragment.read_text(encoding="utf-8"))
            except (OSError, ValueError, ConfigError):
                continue
            for event, groups in (raw.get("hooks") or {}).items():
                for g, group in enumerate(groups):
                    for h, hook in enumerate(group.get("hooks", [])):
                        command = str(hook.get("command", ""))
                        script = SCRIPT.search(command)
                        path = fragment.parent / "hooks" / script[1] if script else None
                        done = rendered["hooks"][event][g]["hooks"][h]["command"]
                        found.append({"kind": "hook", "name": f"{event} [{group.get('matcher', '*')}] "
                                      f"{script[1] if script else command}",
                                      "source": src.key or src.name, "file": src.rel(path if path and path.is_file() else fragment),
                                      "hash": _hash(path) if path and path.is_file() else lock.digest(command.encode()),
                                      "path": tilde(merge.dest), "installed": json.dumps(done)[1:-1] in current})
    return found


def _servers(harness: str, srcs: list[Source]) -> list[dict]:
    found = []
    pins = mcp_pins.read()
    defined = {name: src for src in srcs for name in _registry(src)}
    for sync in mcp_plan(srcs):
        if sync.harness != harness:
            continue
        try:
            current = sync.dest.read_text(encoding="utf-8")
        except OSError:
            current = ""
        for name, s in sorted(sync.servers.items()):
            src = defined.get(name)
            spec = mcp_pins.spec(s) if "command" in s else {"url": lock.clean_url(s["url"])}
            entry = {"kind": "mcp", "name": name, "source": (src.key or src.name) if src else "?",
                     "file": src.rel(src.root / "mcp/servers.toml") if src else "",
                     "hash": lock.digest(json.dumps(spec, sort_keys=True).encode()),
                     "path": tilde(sync.dest), "installed": f'"{name}"' in current or f"[mcp_servers.{name}]" in current,
                     "server": spec}
            pin = pins.get(name)
            if "command" not in s:
                entry["pin"] = "http: not pinned"
            elif not isinstance(pin, dict):
                entry["pin"] = "not pinned"
            else:
                same = {k: pin[k] for k in mcp_pins.SPEC if k in pin} == mcp_pins.spec(s)
                entry["pin"] = f"{len(pin.get('tools', {}))} tool(s) pinned" + ("" if same else ", command changed since")
            found.append(entry)
    return found


def _scrub(value):
    """Every string with the home directory written as ~ (an MCP server's args, a path pack's path)."""
    home = Path.home().as_posix()
    if isinstance(value, str):
        return value.replace(home, "~") if home not in ("", "/") else value
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    return value


def collect() -> dict:
    srcs = sources()
    errors = check_servers(srcs)
    if errors:
        raise ConfigError(errors[0])
    locked = lock.read(lock.user_lock_path()) or {}
    roots = [s.root for s in sources(include_disabled=True)]
    links, _, merges = plan(srcs)
    tools = {}
    for harness in load_harnesses():
        entries = _items(harness, links, srcs, roots) + _hooks(harness, merges, srcs) + _servers(harness, srcs)
        tools[harness] = sorted(entries, key=lambda e: (ORDER.index(e["kind"]), e["source"], e["name"]))
    origins = _origins(srcs, locked)
    for entries in tools.values():
        for e in entries:
            if e["source"] in origins and origins[e["source"]].get("commit"):
                e["commit"] = origins[e["source"]]["commit"]
    return _scrub({"version": 1, "brainrc": ".".join(map(str, core_version())), "scope": "user",
                   "lock": tilde(lock.user_lock_path()) if locked else None,
                   "sources": origins, "tools": tools})


def _text(data: dict) -> None:
    print("brainrc audit: what each tool loads (user scope; reads only, no network)")
    for key, o in data["sources"].items():
        where = o.get("git") or o.get("path") or f"brainrc {o.get('version')}"
        at = f" {o['ref']} at {o['commit'][:12]}" if o.get("ref") and o.get("commit") else (
            f" at {o['commit'][:12]}" if o.get("commit") else "")
        print(f"{'SOURCE':9} {key:9} {where}{at}")
    for harness, entries in data["tools"].items():
        print(f"\n{harness}")
        for e in entries:
            note = "" if e["installed"] else "  (not installed: apply)"
            if e["kind"] == "mcp":
                note = f"  ({e['pin']})" + note
            commit = f"@{e['commit'][:12]}" if e.get("commit") else ""
            print(f"  {e['kind']:7} {e['hash'][:19]}  {e['source'] + commit:22} {e['name']}{note}")
    perms = {k: o["permissions"] for k, o in data["sources"].items() if o.get("permissions")}
    if perms:
        print("\nPermissions (brainrc.lock)")
        for key, fields in perms.items():
            for field, entries in fields.items():
                for entry in entries:
                    print(f"  {key:9} {field:7} {entry}")
    if data["lock"] is None:
        print("\nNo brainrc.lock yet: apply writes it, with each pack's permissions.")


def cmd_audit(as_json: bool = False) -> int:
    try:
        data = collect()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    if as_json:
        print(json.dumps(data, indent=2))
    else:
        _text(data)
    return 0
