"""The manifest: which harnesses apply manages, at which paths, linked from which source roots.

apply writes it to `<settings home>/harnesses.json`; nothing reads it to decide what to sync (that
comes from harnesses.toml and what is installed). It is the record of what brainrc touched, kept
outside any checkout, so later commands (uninstall, repair) still know after the checkout moves.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import settings_home

VERSION = 1


def manifest_file() -> Path:
    return settings_home() / "harnesses.json"


def read_manifest() -> dict:
    """The manifest, or an empty one when it is missing or unreadable."""
    try:
        data = json.loads(manifest_file().read_text())
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        return {"version": VERSION, "roots": [], "harnesses": {}}
    roots = data.get("roots") if isinstance(data.get("roots"), list) else []
    harnesses = data.get("harnesses") if isinstance(data.get("harnesses"), dict) else {}
    return {"version": VERSION, "roots": [r for r in roots if isinstance(r, str)],
            "harnesses": {n: h for n, h in harnesses.items() if isinstance(h, dict)}}


def updated_manifest(managed: dict[str, dict], roots: list[Path], scope: frozenset[str] | None) -> dict:
    """The manifest after an apply that managed `managed` from `roots`. Inside `scope` (every harness
    when None) the entries become `managed`; outside it they stay. Roots accumulate, newest first,
    so a checkout's old location stays on record after it moves."""
    old = read_manifest()
    harnesses = {n: h for n, h in old["harnesses"].items() if scope is not None and n not in scope}
    harnesses.update({n: {k: v for k, v in h.items() if k != "enabled"} for n, h in managed.items()})
    new_roots = [str(r) for r in roots]
    return {"version": VERSION, "roots": new_roots + [r for r in old["roots"] if r not in new_roots],
            "harnesses": dict(sorted(harnesses.items()))}


def write_manifest(data: dict) -> None:
    if manifest_file().is_file() and read_manifest() == data:
        return
    manifest_file().parent.mkdir(parents=True, exist_ok=True)
    tmp = manifest_file().with_name(".harnesses.json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(manifest_file())
