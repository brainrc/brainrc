"""`brainrc update [pack ...]` (#288): the one command that moves a git pack's pinned commit.

apply and install hold each git pack at the commit brainrc.lock records. update refetches the
named packs (or every git pack) at their `ref`, prints what changes before anything is relinked
or relocked (the commits between the old pin and the new one, and the installed files added,
changed or removed), and tells apply which packs moved so it relocks them.
"""
from __future__ import annotations

from pathlib import Path

from . import lock
from .config import ConfigError
from .packs import (
    UPDATE_DEPTH, commits_between, describe, fetch_pack, git_packs, head, pinned,
)
from .project import MANIFEST, find_project, load, project_pack_files
from .sources import load_pack


def _targets() -> list[tuple[str, str, dict, Path, dict | None, object]]:
    """(scope, key, config, clone dir, the lock, files_of) for every git pack: the user scope's,
    then the project's here, if any."""
    found = []
    user_lock = lock.read(lock.user_lock_path())
    for key, cfg, root in git_packs():
        found.append(("user", key, cfg, root, user_lock, lock.user_pack_files))
    here = find_project()
    if here:
        proj = load(here)
        proj_lock = lock.read(proj.lock_path)
        for p in proj.packs():
            if "git" in p.cfg:
                found.append(("project", p.key, p.cfg, p.root, proj_lock,
                              lambda src, proj=proj: project_pack_files(proj, src)))
    return found


def fetch(names: list[str]) -> tuple[frozenset[str], frozenset[str]] | int:
    """Refetch and report each pack; (user keys, project keys) that moved, or an exit code."""
    try:
        targets = _targets()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    known = {t[1] for t in targets}
    unknown = [n for n in names if n not in known]
    if unknown:
        listed = ", ".join(sorted(known)) or "none"
        for n in unknown:
            print(f"ERROR pack {n}: not a git pack here (git packs: {listed})")
        return 2
    moved: dict[str, set[str]] = {"user": set(), "project": set()}
    for scope, key, cfg, root, locked, files_of in targets:
        if names and key not in names:
            continue
        old = pinned(locked, key, cfg) or (head(root) if root.is_dir() else None)
        print(describe(key, cfg))
        try:
            fetch_pack(key, cfg, root, depth=UPDATE_DEPTH)
        except ConfigError as e:
            print(f"ERROR {e}")
            print("\nNothing applied. Fix it, then re-run update; apply keeps every pack at its locked commit.")
            return 1
        entry = (locked or {}).get("packs", {}).get(key)
        report(scope, key, cfg, root, old, entry if pinned(locked, key, cfg) else None, files_of)
        moved[scope].add(key)
    return frozenset(moved["user"]), frozenset(moved["project"])


def report(scope: str, key: str, cfg: dict, root: Path, old: str | None, entry: dict | None, files_of) -> None:
    """The lines update prints for one pack before apply relocks it."""
    new = head(root) or "?"
    ref = str(cfg.get("ref", "HEAD"))
    where = f"({scope} scope)" if scope == "user" else f"(project, {MANIFEST})"
    if old is None:
        print(f"{'PIN':9} {key:9} {ref} at {new[:12]}  {where}")
        return
    if old == new:
        print(f"{'CURRENT':9} {key:9} {ref} at {new[:12]}, no change  {where}")
        return
    print(f"{'MOVED':9} {key:9} {ref}: {old[:12]} -> {new[:12]}  {where}")
    commits = commits_between(root, old, new)
    if commits is None:
        print(f"{'':9} {'commits':9} {old[:12]} isn't in the last {UPDATE_DEPTH} commits of {ref}: "
              "its history was rewritten, or more than that moved")
    for line in commits or []:
        print(f"{'':9} {'commit':9} {line}")
    if entry is None:
        return
    try:
        now = files_of(load_pack(root, key))
    except ConfigError as e:
        print(f"{'':9} {'files':9} can't list them: {e}")
        return
    was = entry.get("files", {})
    for rel in sorted(set(was) | set(now)):
        if rel not in was:
            print(f"{'':9} {'added':9} {rel}")
        elif rel not in now:
            print(f"{'':9} {'removed':9} {rel}")
        elif was[rel] != now[rel]:
            print(f"{'':9} {'changed':9} {rel}")

