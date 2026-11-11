"""The manifest: which harnesses apply manages, at which paths, linked from which source roots.

apply writes it to `<settings home>/harnesses.json`; nothing reads it to decide what to sync (that
comes from harnesses.toml and what is installed). It is the record of what brainrc touched, kept
outside any checkout, so later commands (uninstall, repair) still know after the checkout moves.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import HARNESS_VARS, env_dir, expand, harness_home, settings_home, tilde

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


PATH_KEYS = ("home", "skills", "agents", "commands", "plugin", "instructions", "hooks_dir", "settings", "mcp")


def _inside_home(path: Path) -> bool:
    """True if path is strictly inside the home directory (so never ~, / or one of ~'s ancestors),
    or inside a harness's config dir named by its env var now (e.g. CLAUDE_CONFIG_DIR=/opt/claude)."""
    roots = [Path.home(), *(expand(env_dir(v, "~")) for v in HARNESS_VARS)]
    return path.is_absolute() and any(r != Path("/") and r in path.parents for r in roots)


def checked_manifest() -> tuple[dict, list[str]]:
    """The manifest with what uninstall and repair must not trust left out, and a warning for each.

    A harness entry is dropped when one of its paths is not inside ~, or its hooks_dir is the
    harness home or one of its ancestors (its hook commands would then match the user's own). A
    root is dropped when it is not absolute, or is /, ~ or one of ~'s ancestors."""
    data = read_manifest()
    warnings, harnesses = [], {}
    for name, h in data["harnesses"].items():
        try:
            paths = {k: expand(h[k]) for k in PATH_KEYS if k in h}
            home = harness_home(h)
        except (TypeError, ValueError):
            paths, home = None, None
        bad = None if paths is not None else "a path that isn't a string"
        for key, path in (paths or {}).items():
            if bad is None and not _inside_home(path):
                bad = f"{key} = {h[key]!r} is not inside ~"
        hooks = (paths or {}).get("hooks_dir")
        if bad is None and hooks and home and (hooks == home or hooks in home.parents):
            bad = f"hooks_dir = {h['hooks_dir']!r} is the harness home or holds it"
        if bad:
            warnings.append(f"{tilde(manifest_file())}: ignored harness {name!r}: {bad}")
        else:
            harnesses[name] = h
    roots = []
    for r in data["roots"]:
        root = Path(r)
        if not root.is_absolute() or root == Path.home() or root in Path.home().parents:
            warnings.append(f"{tilde(manifest_file())}: ignored root {r!r}: too broad to trust")
        else:
            roots.append(r)
    return {**data, "roots": roots, "harnesses": harnesses}, warnings


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
