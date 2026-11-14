"""`brainrc audit` (#291): one list of what the agents load. Every skill, agent, command, rule, hook
and MCP server brainrc puts into each harness (tool), with the source it came from, that source's
commit and the item's hash, plus each pack's permissions from brainrc.lock and the MCP tool pins.

It reads only: no network, nothing written. Paths under ~ are written with ~, a URL loses any user
name or password, and an MCP server's environment is named, never read.
"""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

from . import config, lock, mcp_pins
from .config import ConfigError, load_harnesses, tilde
from .mcp import _owned, _registry, check_servers, mcp_plan
from .packs import head
from .plan import Link, plan, render_fragment
from .sources import Source, core_version, item_name, local_rules, markdown_files, rule_text, sources, tree_files

KIND = {"skills": "skill", "agents": "agent", "commands": "command"}
ORDER = ("skill", "agent", "command", "rule", "hook", "mcp")
SCRIPT = re.compile(r"\{\{hooks_dir\}\}/([^\"'\s]+)")
SECRET_FLAG = re.compile(r"(?i)^-{1,2}[\w-]*(token|key|secret|passw|auth|credential)[\w-]*$")
SECRET_PAIR = re.compile(r"(?i)^(-{1,2}[\w-]*(?:token|key|secret|passw|auth|credential)[\w-]*=).+$")


@functools.lru_cache(maxsize=None)
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


def _rules(srcs: list[Source], linked: bool, dest: str) -> list[dict]:
    """Every rule in the instructions file the harness loads, as render_instructions joins them;
    installed when the link is in place and the rendered file holds the rule's text."""
    try:
        rendered = config.rendered_instructions().read_text(encoding="utf-8") if linked else ""
    except OSError:
        rendered = ""
    rules = [(src.key or src.name, src.rel(p), p) for src in srcs for p in markdown_files("rules", src)]
    rules += [("local", tilde(p), p) for p in local_rules(srcs)]
    return [{"kind": "rule", "name": p.stem, "source": source, "file": file, "hash": _hash(p), "path": dest,
             "installed": bool(rendered) and rule_text(p) in rendered} for source, file, p in rules]


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
                for g, group in enumerate(groups if isinstance(groups, list) else []):
                    if not isinstance(group, dict):
                        continue
                    nested = isinstance(group.get("hooks"), list)  # Claude Code nests; Cursor lists each hook
                    for h, hook in enumerate(group["hooks"] if nested else [group]):
                        if not isinstance(hook, dict):
                            continue
                        command = str(hook.get("command") or hook.get("type", "?"))
                        script = SCRIPT.search(command)
                        path = fragment.parent / "hooks" / script[1] if script else None
                        done_group = rendered["hooks"][event][g]
                        done = str((done_group["hooks"][h] if nested else done_group).get("command") or command)
                        found.append({"kind": "hook", "name": f"{event} [{group.get('matcher', '*')}] "
                                      f"{script[1] if script else _redact_cmd(command)}",
                                      "source": src.key or src.name, "file": src.rel(path if path and path.is_file() else fragment),
                                      "hash": _hash(path) if path and path.is_file() else lock.digest(command.encode()),
                                      "path": tilde(merge.dest), "installed": json.dumps(done)[1:-1] in current})
    return found


def _servers(harness: str, srcs: list[Source]) -> list[dict]:
    found = []
    pins, owned = mcp_pins.read(), _owned()
    defined = {name: src for src in srcs for name in _registry(src)}
    for sync in mcp_plan(srcs):
        if sync.harness != harness:
            continue
        for name, s in sorted(sync.servers.items()):
            src = defined.get(name)
            spec = mcp_pins.spec(s) if "command" in s else {"url": s["url"]}
            shown = {**spec, "args": [*_redact(spec["args"])]} if spec.get("args") else dict(spec)
            if "url" in shown:
                shown["url"] = _bare_url(shown["url"])
            entry = {"kind": "mcp", "name": name, "source": (src.key or src.name) if src else "?",
                     "file": src.rel(src.root / "mcp/servers.toml") if src else "",
                     "hash": lock.digest(json.dumps(spec, sort_keys=True).encode()),
                     # brainrc's record of the servers it wrote: a server of yours with the name doesn't count
                     "path": tilde(sync.dest), "installed": name in owned.get(str(sync.dest), []),
                     "server": shown}
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


def _bare_url(url: str) -> str:
    """A URL without user name, password, query or fragment: where tokens ride along."""
    url = lock.clean_url(url)
    base = re.split(r"[?#]", url, maxsplit=1)[0]
    return base + ("?…" if base != url else "")


def _redact(args: list[str]):
    """Arguments with the value of a token, key, secret, password or auth flag shown as `…`."""
    hide = False
    for a in args:
        if hide:
            yield "…"
            hide = False
        elif m := SECRET_PAIR.match(a):
            yield m[1] + "…"
        else:
            hide = bool(SECRET_FLAG.match(a))
            yield a


def _redact_cmd(command: str) -> str:
    return " ".join(_redact(command.split(" ")))


def _scrub(value):
    """Every string with the home directory written as ~ (an MCP server's args, a path pack's path),
    in either separator, and only where the home directory is a whole path prefix."""
    homes = {Path.home().as_posix(), str(Path.home())} - {"", "/", "\\"}
    if isinstance(value, str):
        for home in sorted(homes, key=len, reverse=True):
            value = re.sub(re.escape(home) + r"(?=[/\\]|$)", "~", value)
        return value
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    return value


def collect() -> dict:
    _hash.cache_clear()  # one run's cache: files change between runs
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
