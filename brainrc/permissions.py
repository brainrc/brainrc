"""What a pack can do (#289): its hooks, MCP servers, tool grants and network domains, recorded per
pack in brainrc.lock. `status` lists what is added or removed against the lock, and `apply` asks
before any widening (an added entry) unless --yes; without a terminal to ask in, it refuses.

A machine's first lock (no brainrc.lock yet) has nothing to widen from: its permissions are listed
and recorded as the baseline. A pack entry from a lock written before permissions were recorded
is taken as that baseline only while the pack's files still hash as the lock says.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from .config import KINDS
from .sources import Source, frontmatter, item_name

FIELDS = ("hooks", "mcp", "tools", "domains")
LABEL = {"hooks": "hook", "mcp": "mcp", "tools": "tool", "domains": "domain"}
DOMAIN_GRANT = re.compile(r"\bdomain:([A-Za-z0-9.*-]+)")
URL_HOST = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://(?:[^/@?#]*@)?(\[[^\]/]*\]|[^/:?#]+)")
ASSUME_YES = False  # the test suite sets it; there is no flag or variable for it


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hooks(src: Source) -> tuple[list[str], list[str]]:
    """(hook entries, settings grants) from each overrides/<harness>/settings.fragment.json."""
    hooks, grants = [], []
    for fragment in sorted((src.root / "overrides").glob("*/settings.fragment.json")):
        harness = fragment.parent.name
        try:
            data = json.loads(fragment.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # apply reports invalid JSON before it gets here
        if not isinstance(data, dict):
            continue
        for event, groups in (data.get("hooks") or {}).items() if isinstance(data.get("hooks"), dict) else ():
            for group in groups if isinstance(groups, list) else ():
                if not isinstance(group, dict):
                    continue
                matcher = group.get("matcher", "*")
                for h in group.get("hooks", [group]) if isinstance(group.get("hooks", []), list) else ():
                    if isinstance(h, dict) and "command" in h:
                        hooks.append(f"{harness} {event} [{matcher}] {h['command']}")
        for key, value in data.items():
            if key == "hooks":
                continue
            if key == "permissions" and isinstance(value, dict):
                for kind, rules in sorted(value.items()):
                    for rule in rules if isinstance(rules, list) else [rules]:
                        grants.append(f"{harness} {kind} {rule}")
            else:  # the value too, so a changed command (statusLine, apiKeyHelper) shows as a change
                text = json.dumps(value, sort_keys=True, ensure_ascii=False)
                grants.append(f"{harness} sets {key} = " + (text if len(text) <= 200 else digest(text)))
    return hooks, grants


def _servers(src: Source) -> list[str]:
    from .mcp import _registry  # mcp imports settings, which imports nothing of ours; keep it lazy
    entries = []
    for name, s in sorted(_registry(src).items()):
        if not isinstance(s, dict):
            continue
        what = s.get("url") if "url" in s else " ".join(map(str, [s.get("command", "?"), *s.get("args", [])]))
        extra = []
        if s.get("env_from"):
            extra.append("env " + ", ".join(map(str, s["env_from"])))
        if s.get("harnesses"):
            extra.append("for " + ", ".join(map(str, s["harnesses"])))
        entries.append(f"{name} {what}" + (f" ({'; '.join(extra)})" if extra else ""))
    return entries


def _tools(items: list[Path]) -> list[str]:
    """Each agent's `tools` (an agent without them gets every tool), and each skill's and
    command's `allowed-tools`."""
    found = []
    for path in items:
        if path.is_dir():
            meta, kind, key = frontmatter(path / "SKILL.md"), "skill", "allowed-tools"
        elif path.parent.name == "agents":
            meta, kind, key = frontmatter(path), "agent", "tools"
        elif path.parent.name == "commands":
            meta, kind, key = frontmatter(path), "command", "allowed-tools"
        else:
            continue
        value = meta.get(key, "")
        tools = [t.strip() for t in re.split(r"[,\s]+(?![^()]*\))", value.strip("[]")) if t.strip()]
        if kind == "agent" and not tools:
            tools = ["(every tool)"]
        found += [f"{kind} {item_name(path)}: {t.strip(chr(34) + chr(39))}" for t in tools]
    return found


def _domains(servers: dict, grants: list[str]) -> list[str]:
    hosts = set()
    for s in servers.values():
        if isinstance(s, dict) and isinstance(s.get("url"), str):
            m = URL_HOST.match(s["url"])
            if m:
                hosts.add(m[1].lower())
    for g in grants:
        hosts.update(DOMAIN_GRANT.findall(g))
    return sorted(hosts)


def of_pack(src: Source, items: list[Path], hooks: bool, mcp: bool) -> dict[str, list[str]]:
    """The pack's permissions as the lock records them: only what this scope installs."""
    hook_entries, settings = _hooks(src) if hooks else ([], [])
    if isinstance(src.meta.get("validator"), str):  # pack code brainrc itself runs, in every scope
        hook_entries.append(f"brainrc validator {src.meta['validator']}")
    from .mcp import _registry
    servers = _registry(src) if mcp else {}
    tools = _tools(items) + settings
    data = {"hooks": hook_entries, "mcp": _servers(src) if mcp else [], "tools": tools,
            "domains": _domains(servers, tools)}
    return {k: sorted(set(v)) for k, v in data.items() if v}


def user_items(src: Source) -> list[Path]:
    from .sources import installed_items
    return [p for kind in KINDS for p in installed_items(src, kind)]


def baseline(old: dict | None, key: str, entry: dict) -> dict[str, list[str]]:
    """What the lock says this pack could already do: nothing for a new pack. A lock written
    before permissions were recorded vouches for them only while the pack's files are unchanged."""
    was = (old or {}).get("packs", {}).get(key)
    if was is None:
        return {}
    if "permissions" in was:
        return was["permissions"]
    if was.get("files") != entry.get("files"):
        return {}
    # mcp/servers.toml isn't among the hashed files, so servers and their hosts are never vouched for
    perms = entry.get("permissions", {})
    hosts = {e for e in perms.get("domains", []) if any(f"domain:{e}" in t for t in perms.get("tools", []))}
    return {k: v for k, v in {**perms, "mcp": [], "domains": sorted(hosts)}.items() if v}


def diff(old_lock: dict | None, packs: dict[str, dict]) -> list[tuple[str, str, str, str]]:
    """(pack, "+" or "-", field, entry) for each change against the lock, by pack then field.
    packs: the new lock's pack entries, each with `files` and `permissions`. No lock at all is a
    first install: nothing to widen from, so no change."""
    if old_lock is None:
        return []
    changes = []
    for key in sorted(set(packs) | set(old_lock.get("packs", {}))):
        new = packs.get(key, {}).get("permissions", {})
        was = baseline(old_lock, key, packs[key]) if key in packs else old_lock["packs"][key].get("permissions", {})
        for field in FIELDS:
            a, b = set(was.get(field, [])), set(new.get(field, []))
            changes += [(key, "-", field, e) for e in sorted(a - b)]
            changes += [(key, "+", field, e) for e in sorted(b - a)]
    return changes


def report(changes: list[tuple[str, str, str, str]], label: str = "") -> None:
    for key, sign, field, entry in changes:
        note = "  (a removed restriction: it widens)" if sign == "-" and _widening(sign, field, entry) else ""
        print(f"{'PERMS':9} {key:9} {sign} {LABEL[field]:6} {entry}{note}" + (f"  ({label})" if label else ""))


def first(packs: dict[str, dict], label: str) -> None:
    """A first install: list what each pack can do, so it is seen once before it is the baseline."""
    for key, entry in sorted(packs.items()):
        for field in FIELDS:
            for e in entry.get("permissions", {}).get(field, []):
                print(f"{'PERMS':9} {key:9} {LABEL[field]:8} {e}  ({label})")


def interactive() -> bool:
    """A person at a terminal can answer: stdin and stdout are both a terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def widens(changes) -> bool:
    """An added entry, or a removed deny or ask rule: either lets the pack do more."""
    return any(_widening(sign, field, entry) for _, sign, field, entry in changes)


def _widening(sign: str, field: str, entry: str) -> bool:
    if sign == "+":
        return True
    return field == "tools" and len(entry.split(" ", 2)) == 3 and entry.split(" ", 2)[1] in ("deny", "ask")


def confirm(changes, yes: bool, where: str) -> bool:
    """True if the widening may be applied: --yes, or a yes typed at a terminal. A run without a
    terminal (CI, a script, a pipe) and without --yes refuses."""
    if yes or ASSUME_YES:
        return True
    added = sum(_widening(sign, field, entry) for _, sign, field, entry in changes)
    if not interactive():
        print(f"\nNothing written{where}. The packs would widen {added} permission(s) (PERMS above), and "
              "there is no terminal to ask in. Re-run with --yes to accept them.")
        return False
    try:
        answer = input(f"\nThe packs widen {added} permission(s) (PERMS above). Apply them? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() in ("y", "yes"):
        return True
    print(f"Nothing written{where}.")
    return False

