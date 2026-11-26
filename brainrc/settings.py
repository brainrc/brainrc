"""Merging brainrc's hooks, and the packs' permission entries, into a harness settings file.

Hook groups are brainrc's by where their command lives (OWNED_HOOK). Permission entries
(`permissions.allow`, `deny` and `ask` in a settings fragment, #142) and sandbox entries (packs'
path and host guard rules, #322) are plain strings a user could have written too, so the ones
brainrc added are recorded per file in
$BRAINRC_HOME/settings-owned.json: a later apply removes exactly those it no longer wants, and an
entry the user had first is never brainrc's to remove.
"""
from __future__ import annotations

import copy
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path

from . import adapters
from .config import BACKUPS_KEPT, OWNED_HOOK, settings_home
from .plan import SettingsMerge

PERMISSION_LISTS = ("allow", "deny", "ask")
# The OS sandbox's lists packs' path and host guard rules compile to (#322), owned like permission
# entries, under the kind `sandbox.<section>.<key>`.
SANDBOX_LISTS = (("filesystem", "denyRead"), ("filesystem", "denyWrite"), ("network", "deniedDomains"))
SANDBOX_KINDS = tuple(f"sandbox.{section}.{key}" for section, key in SANDBOX_LISTS)


def _owned(group: dict, markers: set[str] = frozenset()) -> bool:
    # Claude groups hold their commands under "hooks"; Cursor's entries are flat {command}s.
    for h in [group, *group.get("hooks", [])]:
        command = str(h.get("command", ""))
        if OWNED_HOOK.search(command) or any(m in command for m in markers):
            return True
    return False


def merge_settings(current: dict, fragment: dict, markers: set[str] = frozenset(),
                   owned: dict[str, list[str]] | None = None) -> dict:
    """Return current with brainrc's hook groups replaced by the fragment's.

    Hook groups owned by other tools/plugins are kept in place and order. The fragment's
    permission entries are added, and those in `owned` (added by an earlier apply) that it no
    longer lists are removed. Its other keys (Cursor's `version`) are only set when missing; the
    rest stays under user control.
    """
    merged = copy.deepcopy(current)
    for key, value in fragment.items():
        if key not in ("hooks", "permissions", "sandbox"):
            merged.setdefault(key, copy.deepcopy(value))
    _merge_permissions(merged, current, fragment.get("permissions"), owned or {})
    _merge_sandbox(merged, current, fragment.get("sandbox"), owned or {})
    hooks = merged.setdefault("hooks", {})
    wanted = fragment.get("hooks", {})
    for event in [*hooks, *(e for e in wanted if e not in hooks)]:  # existing first, then fragment order
        kept = [g for g in hooks.get(event, []) if not _owned(g, markers)]
        groups = kept + copy.deepcopy(wanted.get(event, []))
        if groups:
            hooks[event] = groups
        else:
            hooks.pop(event, None)
    if not hooks and current.get("hooks") != {}:  # drop the key brainrc emptied, keep a user's own {}
        merged.pop("hooks")
    return merged


def _entries(perms, kind: str) -> list[str]:
    value = perms.get(kind) if isinstance(perms, dict) else None
    return [e for e in value if isinstance(e, str)] if isinstance(value, list) else []


def _merge_permissions(merged: dict, current: dict, wanted, owned: dict[str, list[str]]) -> None:
    """Add the wanted permission entries, drop the owned ones no longer wanted, keep the user's."""
    wanted = wanted if isinstance(wanted, dict) else {}
    perms = merged.get("permissions")
    if perms is not None and not isinstance(perms, dict):
        return  # not an object: the user's to fix, so leave it as it is
    perms = copy.deepcopy(perms or {})
    for key, value in wanted.items():  # e.g. defaultMode: the user's own value wins, as before
        if key not in PERMISSION_LISTS:
            perms.setdefault(key, copy.deepcopy(value))
    for kind in PERMISSION_LISTS:
        have = perms.get(kind)
        if have is not None and not isinstance(have, list):
            continue  # not a list: the user's to fix, so leave it as it is
        want = list(dict.fromkeys(_entries(wanted, kind)))
        gone = set(owned.get(kind, [])) - set(want)
        entries = [e for e in (have or []) if not (isinstance(e, str) and e in gone)]
        entries += [e for e in want if e not in entries]
        if entries or have == []:  # a user's own empty list stays
            perms[kind] = entries
        else:
            perms.pop(kind, None)  # brainrc emptied it, or never had one to add
    if perms or current.get("permissions") == {}:
        merged["permissions"] = perms
    else:
        merged.pop("permissions", None)


def _merge_list(container: dict, key: str, want: list[str], gone: set[str]) -> None:
    """container[key]: drop the gone entries, add the wanted ones, keep the user's; a user's own
    empty list stays, and one brainrc emptied goes. A value that isn't a list is left as it is."""
    have = container.get(key)
    if have is not None and not isinstance(have, list):
        return  # the user's to fix
    entries = [e for e in (have or []) if not (isinstance(e, str) and e in gone)]
    entries += [e for e in want if e not in entries]
    if entries or have == []:
        container[key] = entries
    else:
        container.pop(key, None)


def _sandbox_entries(box, kind: str) -> list[str]:
    _, section, key = kind.split(".")
    part = box.get(section) if isinstance(box, dict) else None
    return _entries(part, key)


def _merge_sandbox(merged: dict, current: dict, wanted, owned: dict[str, list[str]]) -> None:
    """Add the wanted sandbox entries, drop the owned ones no longer wanted, keep the user's; a
    fragment's other sandbox keys (enabled) are only set when missing."""
    wanted = wanted if isinstance(wanted, dict) else {}
    box = merged.get("sandbox")
    if box is not None and not isinstance(box, dict):
        return  # not an object: the user's to fix
    box = copy.deepcopy(box or {})
    for key, value in wanted.items():
        if key not in {section for section, _ in SANDBOX_LISTS}:
            box.setdefault(key, copy.deepcopy(value))
    had = current.get("sandbox") if isinstance(current.get("sandbox"), dict) else {}
    for section in dict.fromkeys(section for section, _ in SANDBOX_LISTS):
        part = box.get(section)
        if part is not None and not isinstance(part, dict):
            continue
        part = dict(part or {})
        extra = wanted.get(section) if isinstance(wanted.get(section), dict) else {}
        for key, value in extra.items():  # e.g. network.allowLocalBinding from a fragment
            if not isinstance(value, list):
                part.setdefault(key, copy.deepcopy(value))
        for sec, key in SANDBOX_LISTS:
            if sec == section:
                kind = f"sandbox.{sec}.{key}"
                want = list(dict.fromkeys(_sandbox_entries(wanted, kind)))
                _merge_list(part, key, want, set(owned.get(kind, [])) - set(want))
        if part or had.get(section) == {}:
            box[section] = part
        else:
            box.pop(section, None)
    if box or current.get("sandbox") == {}:
        merged["sandbox"] = box
    else:
        merged.pop("sandbox", None)


def owned_permissions(current: dict, fragment: dict, owned: dict[str, list[str]] | None) -> dict[str, list[str]]:
    """The permission and sandbox entries brainrc owns after merging fragment into current: each
    wanted entry it owned before or that current didn't have (an entry the user had first stays
    theirs)."""
    owned = owned or {}
    perms = current.get("permissions")
    result = {}
    for kind in PERMISSION_LISTS:
        had = set(_entries(perms, kind))
        mine = [e for e in dict.fromkeys(_entries(fragment.get("permissions"), kind))
                if e in owned.get(kind, []) or e not in had]
        if mine:
            result[kind] = mine
    for kind in SANDBOX_KINDS:
        had = set(_sandbox_entries(current.get("sandbox"), kind))
        mine = [e for e in dict.fromkeys(_sandbox_entries(fragment.get("sandbox"), kind))
                if e in owned.get(kind, []) or e not in had]
        if mine:
            result[kind] = mine
    return result


def owned_file() -> Path:
    return settings_home() / "settings-owned.json"


def read_owned(dest: Path) -> dict[str, list[str]]:
    """The permission entries an earlier apply added to dest, by kind ({} when none)."""
    try:
        data = json.loads(owned_file().read_text())
    except (OSError, ValueError):
        return {}
    entry = data.get(str(dest)) if isinstance(data, dict) else None
    perms = entry.get("permissions") if isinstance(entry, dict) else None
    found = {k: _entries(perms, k) for k in PERMISSION_LISTS if _entries(perms, k)}
    box = entry.get("sandbox") if isinstance(entry, dict) else None
    for kind in SANDBOX_KINDS:  # recorded as {"filesystem.denyRead": [...]}
        if entries := _entries(box, kind.split(".", 1)[1]):
            found[kind] = entries
    return found


def record_owned(dest: Path, owned: dict[str, list[str]]) -> None:
    """Write dest's entry in settings-owned.json, dropping it (and the file, once empty) when none."""
    try:
        data = json.loads(owned_file().read_text())
    except (OSError, ValueError):
        data = {}
    data = data if isinstance(data, dict) else {}
    if owned:
        perms = {k: v for k, v in owned.items() if k in PERMISSION_LISTS}
        box = {k.split(".", 1)[1]: v for k, v in owned.items() if k in SANDBOX_KINDS}
        data[str(dest)] = {**({"permissions": perms} if perms else {}), **({"sandbox": box} if box else {})}
    else:
        data.pop(str(dest), None)
    if data:
        owned_file().parent.mkdir(parents=True, exist_ok=True)
        owned_file().write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    elif owned_file().is_file():
        owned_file().unlink()


def as_claude(current: dict, fmt: str) -> dict:
    """A settings file in Claude Code's shape, hooks under "hooks", whatever its own format: the
    format's adapter maps it (#306), e.g. Antigravity's named hook sets."""
    return adapters.settings_adapter(fmt).hooks_view(current)


def from_claude(current: dict, merged: dict, fmt: str) -> dict:
    """current with the hooks in merged (Claude Code's shape) put back in fmt's place."""
    return adapters.settings_adapter(fmt).hooks_put(current, merged)


def settings_change(m: SettingsMerge) -> tuple[str, dict | None]:
    """Return (state, merged) where state is ok | merge | conflict."""
    try:
        current = json.loads(m.dest.read_text()) if m.dest.exists() else {}
    except json.JSONDecodeError:
        return ("ok" if _nothing_to_remove(m) else "conflict"), None
    if not isinstance(current, dict):
        return "conflict", None
    if adapters.settings_adapter(m.fmt).hooks_problem(current):
        return ("ok" if _nothing_to_remove(m) else "conflict"), None
    view = as_claude(current, m.fmt)
    merged = from_claude(current, merge_settings(view, m.wanted(), m.markers(), read_owned(m.dest)), m.fmt)
    return ("ok" if merged == current else "merge"), merged


def _nothing_to_remove(m: SettingsMerge) -> bool:
    """A lenient merge that only takes brainrc's hooks out, of a file brainrc can't parse that
    holds nothing of brainrc's: no hook command of its and no recorded entry. A tool brainrc
    doesn't manage, such as Gemini CLI with a settings.json with comments, is then left alone."""
    if not m.lenient or m.fragments or m.sandbox or any(read_owned(m.dest).values()):
        return False
    try:
        text = m.dest.read_text()
    except OSError:
        return False
    return not OWNED_HOOK.search(text) and not any(marker in text for marker in m.markers())


def conflict_reason(m: SettingsMerge) -> str:
    """Why settings_change returned conflict, for the message: bad JSON or a wrong-shaped entry."""
    try:
        current = json.loads(m.dest.read_text())
    except (OSError, ValueError):
        return "invalid JSON"
    if not isinstance(current, dict):
        return "not a JSON object"
    return adapters.settings_adapter(m.fmt).hooks_problem(current) or "invalid JSON"


def settings_owned(m: SettingsMerge) -> dict[str, list[str]]:
    """What settings-owned.json should record for m.dest after apply merges it."""
    try:
        current = json.loads(m.dest.read_text()) if m.dest.exists() else {}
    except (OSError, ValueError):
        return read_owned(m.dest)
    return owned_permissions(current if isinstance(current, dict) else {}, m.wanted(), read_owned(m.dest))


class FileChanged(Exception):
    """The file changed after apply read it: a running harness wrote it meanwhile."""


def read_current(path: Path) -> str | None:
    """The file's text as apply first saw it (None: absent), for replace_file's `before`."""
    return path.read_text() if path.is_file() else None


def write_settings(dest: Path, merged: dict, before: str | None) -> None:
    replace_file(dest, json.dumps(merged, indent=2) + "\n", before)


def replace_file(dest: Path, text: str, before: str | None) -> None:
    """Back up, prune old backups, then replace atomically so a crash never leaves half a file.

    A symlinked dest is written through to its target, which keeps the link. The target's mode is
    kept on the new file and the backup. Raises FileChanged, writing nothing, when the file no
    longer holds `before`.
    """
    target = dest.resolve()  # non-strict: a dangling link resolves to the file it would create
    if read_current(target) != before:
        raise FileChanged(dest)
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
    if mode is not None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        _create(target.with_name(f"{target.name}.bak-brainrc-{stamp}"), target.read_bytes(), mode)
        # Old backups carry the former name; order both by the timestamp at the end of the name.
        # Only real files named exactly like a backup count: a user's look-alike is never pruned.
        backup = re.compile(rf"{re.escape(target.name)}\.bak-(?:brainrc|aicfg)-\d{{8}}T\d{{6}}Z")
        backups = sorted(
            (p for p in target.parent.glob(f"{target.name}.bak-*")
             if backup.fullmatch(p.name) and not p.is_symlink() and p.is_file()),
            key=lambda p: (p.name.rsplit("-", 1)[-1], p.name),
        )
        for old in backups[:-BACKUPS_KEPT]:
            old.unlink()
    tmp = target.with_name(f".{target.name}.brainrc-tmp-{os.getpid()}")
    _create(tmp, text.encode(), mode)
    os.replace(tmp, target)


def _create(path: Path, data: bytes, mode: int | None) -> None:
    """Write a fresh file that is never looser than 0600 before it gets mode (None: umask default)."""
    path.unlink(missing_ok=True)  # an existing file would keep its own mode under O_TRUNC
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666 if mode is None else 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    if mode is not None:
        os.chmod(path, mode)
