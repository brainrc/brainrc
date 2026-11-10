"""uninstall: take out everything apply put into the harnesses, and nothing else.

Removes the links brainrc made (dangling ones too), its hook groups in each settings file, the
MCP servers it added, and the files and directories that leaves empty. Harness paths come from
the manifest apply wrote (#126) as well as harnesses.toml, and a link counts as brainrc's when it
points into any source root the manifest ever recorded, so uninstall still works after the
checkout or a pack is moved or deleted. An instructions file `init` moved aside is put back.
`--purge` also deletes the settings home: local config, rendered files and fetched git packs.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import config
from .config import (
    KINDS,
    ConfigError,
    expand,
    former_hooks_dirs,
    former_plugin_paths,
    harness_home,
    hooks_copy_root,
    home_extensions_file,
    load_harnesses,
    rendered_agents_dir,
    rendered_instructions,
    settings_home,
    tilde,
)
from .manifest import manifest_file, read_manifest
from .mcp import ADAPTERS, McpSync, _owned_file, _read_record, mcp_change, record_owned, write_mcp
from .plan import SettingsMerge, _managed_target, link_target
from .settings import FileChanged, read_current, settings_change, write_settings
from .sources import sources

BACKUP = r"\.bak-brainrc-\d{8}T\d{6}Z"


@dataclass
class Step:
    action: str  # REMOVE, RESTORE, UNMERGE, DELETE, RMDIR, PURGE
    harness: str
    path: Path
    run: Callable[[], None]
    note: str = ""
    removes: set[Path] = field(default_factory=set)  # paths gone afterwards, for the empty-dir check


def _harness_configs() -> tuple[list[tuple[str, dict]], list[str]]:
    """Every harness config to clean: what apply recorded, and what harnesses.toml says now."""
    configs = list(read_manifest()["harnesses"].items())
    warnings = []
    try:
        configs += list(load_harnesses(include_disabled=True).items())
    except ConfigError as e:
        warnings.append(f"{e} (using the paths apply recorded in {tilde(manifest_file())})")
    return configs, warnings


def _roots() -> list[Path]:
    roots = [Path(r) for r in read_manifest()["roots"]] + [config.REPO]
    try:
        roots += [s.root for s in sources(include_disabled=True)]
    except ConfigError:
        pass
    return list(dict.fromkeys(roots))


def _symlinks_in(d: Path) -> list[Path]:
    return sorted(p for p in d.iterdir() if p.is_symlink()) if d.is_dir() and not d.is_symlink() else []


def _link_candidates(h: dict) -> list[Path]:
    """Paths in this harness where apply may have put a link."""
    found = [p for kind in KINDS if kind in h for p in _symlinks_in(expand(h[kind]))]
    if "instructions" in h:
        found.append(expand(h["instructions"]))
    if "plugin" in h:
        found += [expand(p) for p in [h["plugin"], *former_plugin_paths(h["plugin"])]]
    if "hooks_dir" in h:  # core's hooks dir, each pack's sibling, and the pre-rename names
        found += _symlinks_in(expand(h["hooks_dir"]).parent)
    return found


def _init_backup(path: Path) -> Path | None:
    """The newest copy of path that `brainrc init` moved aside."""
    pattern = re.compile(re.escape(path.name) + BACKUP)
    backups = sorted(p for p in path.parent.glob(f"{path.name}.bak-brainrc-*") if pattern.fullmatch(p.name)) \
        if path.parent.is_dir() else []
    return backups[-1] if backups else None


def _fragment_extras(name: str) -> dict:
    """The keys besides hooks that core's fragment adds to a settings file (Cursor's version)."""
    try:
        fragment = json.loads((config.REPO / "overrides" / name / "settings.fragment.json").read_text())
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in fragment.items() if k != "hooks"} if isinstance(fragment, dict) else {}


def _set_aside(path: Path) -> None:
    """Delete a file that holds nothing of the user's, keeping it as a backup like apply does."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.rename(path, path.with_name(f"{path.name}.bak-brainrc-{stamp}"))


def _settings_steps(name: str, h: dict, problems: list[str]) -> list[Step]:
    dest = expand(h["settings"])
    if not dest.is_file():
        return []
    markers = set()
    if "hooks_dir" in h:
        markers = {h["hooks_dir"], *former_hooks_dirs(h["hooks_dir"])}
    m = SettingsMerge(name, dest, [], markers)
    state, merged = settings_change(m)
    if state == "conflict":
        problems.append(f"{tilde(dest)}: invalid JSON, so brainrc's hooks are still in it; fix it by hand, then re-run")
        return []
    if state == "ok":
        return []
    before = read_current(dest)
    if not merged or merged == _fragment_extras(name):
        return [Step("DELETE", name, dest, lambda: _set_aside(dest), "only brainrc's hooks were in it", {dest})]

    def unmerge() -> None:
        write_settings(dest, merged, before)
    return [Step("UNMERGE", name, dest, unmerge, "hooks")]


def _mcp_steps(name: str, h: dict, problems: list[str]) -> list[Step]:
    dest = expand(h["mcp"])
    if name not in ADAPTERS or not dest.is_file():
        return []
    m = McpSync(name, dest, {})
    state, text, _, _ = mcp_change(m)
    if state == "invalid":
        problems.append(f"{tilde(dest)}: can't parse it, so brainrc's MCP servers are still in it; fix it by hand, then re-run")
        return []
    if state == "ok":
        return []
    before = read_current(dest)
    if text.strip() in ("", "{}"):
        def delete() -> None:
            _set_aside(dest)
            record_owned(m, [])
        return [Step("DELETE", name, dest, delete, "only brainrc's MCP servers were in it", {dest})]
    return [Step("UNMERGE", name, dest, lambda: write_mcp(m, text, [], before), "mcp")]


def _generated() -> list[Path]:
    """What apply generates in the settings home; local config and fetched packs stay."""
    return [p for p in (rendered_instructions(), home_extensions_file(), manifest_file())
            if p.is_file()] + [d for d in (rendered_agents_dir(), hooks_copy_root()) if d.is_dir()]


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _empty_after(d: Path, gone: set[Path]) -> bool:
    """True if d holds nothing once every path in gone is removed."""
    return d.is_dir() and not d.is_symlink() and all(
        p in gone or _empty_after(p, gone) for p in d.iterdir())


def _empty_dirs(starts: list[tuple[str, Path, Path]], gone: set[Path]) -> list[Step]:
    """Directories left empty, from each removed path up to (never including) its stop dir."""
    steps, seen = [], set()
    for harness, path, stop in starts:
        d = path.parent
        while d != stop and d not in seen and stop in d.parents and _empty_after(d, gone):
            seen.add(d)
            gone.add(d)
            steps.append(Step("RMDIR", harness, d, lambda d=d: d.rmdir()))
            d = d.parent
    return steps


def plan_uninstall(purge: bool = False) -> tuple[list[Step], list[str], list[str]]:
    """(steps in the order to run them, warnings, problems that stop part of the uninstall)."""
    configs, warnings = _harness_configs()
    roots = _roots()
    problems: list[str] = []
    steps: list[Step] = []
    starts: list[tuple[str, Path, Path]] = []  # (harness, removed path, dir never removed)
    seen: set[Path] = set()
    removed: set[Path] = set()
    home = Path.home()
    for name, h in configs:
        stop = harness_home(h) or home
        for p in _link_candidates(h):
            if p in seen or not p.is_symlink() or not _managed_target(link_target(p), roots):
                continue
            seen.add(p)
            removed.add(p)
            steps.append(Step("REMOVE", name, p, p.unlink, removes={p}))
            starts.append((name, p, stop))
        if "instructions" in h:
            path = expand(h["instructions"])
            backup = _init_backup(path)
            if backup and not any(s.action == "RESTORE" and s.path == path for s in steps) \
                    and (path in removed or not os.path.lexists(path)):
                steps.append(Step("RESTORE", name, path, lambda b=backup, p=path: os.rename(b, p),
                                  f"from {backup.name}, which init moved aside"))
    for name, h in configs:
        for key, make in (("settings", _settings_steps), ("mcp", _mcp_steps)):
            if key in h and expand(h[key]) not in seen:
                seen.add(expand(h[key]))
                for step in make(name, h, problems):
                    steps.append(step)
                    starts += [(name, p, harness_home(h) or home) for p in step.removes]
    restored = {s.path for s in steps if s.action == "RESTORE"}
    gone = {p for s in steps for p in s.removes} - restored
    steps += _empty_dirs([s for s in starts if s[1] not in restored], gone)
    if purge:
        if settings_home().exists():
            steps.append(Step("PURGE", "", settings_home(), lambda: shutil.rmtree(settings_home()),
                              "local config, rendered files and fetched packs"))
    else:
        generated = _generated()
        steps += [Step("REMOVE", "", p, lambda p=p: _remove(p), removes={p}) for p in generated]
        gone |= set(generated)
        steps += _empty_dirs([("", p, settings_home()) for p in generated], gone)
    return steps, warnings, problems


def cmd_uninstall(dry_run: bool = False, purge: bool = False) -> int:
    steps, warnings, problems = plan_uninstall(purge)
    for w in warnings:
        print(f"WARN {w}")
    changed = []
    for step in steps:
        note = f"  ({step.note})" if step.note else ""
        print(f"{step.action:9} {step.harness:9} {tilde(step.path)}{note}")
        if dry_run:
            continue
        try:
            step.run()
        except FileChanged:
            changed.append(step.path)
            print(f"{'CHANGED':9} {step.harness:9} {tilde(step.path)}  (it changed while uninstall ran; left alone)")
    if not dry_run and not purge and _owned_file().is_file() and not _read_record(_owned_file()):
        _owned_file().unlink()  # every server it recorded is gone
    for p in problems:
        print(f"ERROR {p}")
    if not steps and not problems:
        print("Nothing to uninstall: brainrc has nothing in any harness.")
    elif dry_run:
        print(f"\nDry run. Run `{config.command('uninstall')}` to remove them.")
    else:
        print("\nUninstalled. The backups brainrc made (*.bak-brainrc-*) are kept beside each file.")
        if not purge and any(p.name != "apply.lock" for p in settings_home().glob("*")):
            print(f"Your local config and packs are still in {tilde(settings_home())}; "
                  f"`{config.command('uninstall --purge')}` deletes them too.")
        if changed:
            print("Close Claude Code (it rewrites ~/.claude.json while running), then re-run.")
    return 1 if problems or changed else 0
