"""Merging ai-config's hooks into a harness settings file."""
from __future__ import annotations

import copy
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from .config import BACKUPS_KEPT, OWNED_HOOK
from .plan import SettingsMerge


def _owned(group: dict, markers: set[str] = frozenset()) -> bool:
    # Claude groups hold their commands under "hooks"; Cursor's entries are flat {command}s.
    for h in [group, *group.get("hooks", [])]:
        command = str(h.get("command", ""))
        if OWNED_HOOK.search(command) or any(m in command for m in markers):
            return True
    return False


def merge_settings(current: dict, fragment: dict, markers: set[str] = frozenset()) -> dict:
    """Return current with ai-config's hook groups replaced by the fragment's.

    Hook groups owned by other tools/plugins are kept in place and order. The fragment's other
    keys (Cursor's `version`) are only set when missing; the rest stays under user control.
    """
    merged = copy.deepcopy(current)
    for key, value in fragment.items():
        if key != "hooks":
            merged.setdefault(key, copy.deepcopy(value))
    hooks = merged.setdefault("hooks", {})
    wanted = fragment.get("hooks", {})
    for event in [*hooks, *(e for e in wanted if e not in hooks)]:  # existing first, then fragment order
        kept = [g for g in hooks.get(event, []) if not _owned(g, markers)]
        groups = kept + copy.deepcopy(wanted.get(event, []))
        if groups:
            hooks[event] = groups
        else:
            hooks.pop(event, None)
    if not hooks and current.get("hooks") != {}:  # drop the key ai-config emptied, keep a user's own {}
        merged.pop("hooks")
    return merged


def settings_change(m: SettingsMerge) -> tuple[str, dict | None]:
    """Return (state, merged) where state is ok | merge | conflict."""
    try:
        current = json.loads(m.dest.read_text()) if m.dest.exists() else {}
    except json.JSONDecodeError:
        return "conflict", None
    merged = merge_settings(current, m.wanted(), m.markers())
    return ("ok" if merged == current else "merge"), merged


def write_settings(dest: Path, merged: dict) -> None:
    replace_file(dest, json.dumps(merged, indent=2) + "\n")


def replace_file(dest: Path, text: str) -> None:
    """Back up, prune old backups, then replace atomically so a crash never leaves half a file.

    A symlinked dest is written through to its target, which keeps the link. The target's mode is
    kept on the new file and the backup.
    """
    target = dest.resolve()  # non-strict: a dangling link resolves to the file it would create
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
    if mode is not None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        _create(target.with_name(f"{target.name}.bak-aicfg-{stamp}"), target.read_bytes(), mode)
        backups = sorted(target.parent.glob(f"{target.name}.bak-aicfg-*"))
        for old in backups[:-BACKUPS_KEPT]:
            old.unlink()
    tmp = target.with_name(f".{target.name}.aicfg-tmp")
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
