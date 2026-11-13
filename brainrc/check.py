"""`brainrc check` (#285): fail when what's on disk drifted from brainrc.lock. No network, no writes.

In a project it checks, in order: brainrc.toml names the packs the lock does, from the same places;
each pack this machine has (a path pack, or a git clone at the locked commit) hashes as the lock
says; and every file brainrc owns in the repo, and its block in AGENTS.md, hashes as the lock says.
A git pack not fetched here is checked only through the repo's files. A tag or branch whose clone
is now at another commit is reported as MOVED and doesn't fail: the lock still says what to install.
"""
from __future__ import annotations

from pathlib import Path

from . import lock
from .config import ConfigError, _layered, tilde
from .frozen import compare_config, diff_files, diff_outputs
from .packs import head
from .project import BLOCK, MANIFEST, _read, _unit, last_written, load, outputs, planned, project_pack_files
from .sources import _pack_root, load_pack, tree_files


def _pack(key: str, cfg: dict, root: Path, entry: dict, files_of, notes: list[str]):
    """(errors, the loaded pack or None when it can't be checked on this machine)."""
    if "git" in cfg:
        if not root.is_dir():
            notes.append(f"pack {key}: not fetched on this machine; checked through its files in the repo")
            return [], None
        commit = head(root)
        if commit != entry["commit"]:
            lock.report_moved({"packs": {key: entry}}, {"packs": {key: {**entry, "commit": commit or "?"}}},
                              "install --frozen keeps the lock's")
            return [], None
    elif not root.is_dir():
        return [f"pack {key}: no directory at {tilde(root)}"], None
    try:
        src = load_pack(root, key)
    except ConfigError as e:
        return [str(e)], None
    return diff_files(key, entry["files"], files_of(src)), src


def _repo(root: Path, locked: dict, tops: list[str]) -> list[str]:
    """Each file brainrc owns in the repo that differs from the lock, is missing, or was added to a
    skill directory brainrc owns."""
    errors = []
    mine = last_written(root)  # brainrc's own older output is stale, not someone else's file
    stale = " (brainrc wrote it for another lock; `install --frozen` updates it)"
    foreign = " and isn't brainrc's output (`install --frozen` refuses it without --force)"
    owned = locked.get("outputs", {})
    for rel, want in sorted(owned.items()):
        data = _read(root / rel)
        if data is None:
            errors.append(f"{rel}: missing (brainrc.lock lists it)")
        elif lock.digest(data) != want:
            errors.append(f"{rel}: differs from {lock.NAME}"
                          + (stale if lock.digest(data) == mine["outputs"].get(rel) else foreign))
    skills = sorted({_unit(rel, tops).rstrip("/") for rel in owned if _unit(rel, tops) != rel})
    for skill in skills:
        if (root / skill).is_dir() and not (root / skill).is_symlink():
            errors += [f"{skill}/{rel}: not in {lock.NAME}" for rel, _ in tree_files(root / skill)
                       if f"{skill}/{rel}" not in owned]
    for rel, want in sorted(locked.get("blocks", {}).items()):
        data = _read(root / rel)
        m = BLOCK.search(data.decode("utf-8")) if data is not None else None
        if m is None:
            errors.append(f"{rel}: brainrc's block is missing")
        elif lock.digest(m.group(0).encode("utf-8")) != want:
            ours = lock.digest(m.group(0).encode("utf-8")) == mine["blocks"].get(rel)
            errors.append(f"{rel}: brainrc's block differs from {lock.NAME}" + (stale if ours else foreign))
    return errors


def _report(errors: list[str], notes: list[str], fix: str) -> int:
    for n in notes:
        print(f"NOTE {n}")
    for e in errors:
        print(f"DRIFT {e}")
    if errors:
        print(f"\n{len(errors)} difference{'s' if len(errors) != 1 else ''} from {lock.NAME}. {fix}")
        return 1
    print(f"In sync with {lock.NAME}.")
    return 0


def project(root: Path) -> int:
    print(f"\nProject {tilde(root)} ({MANIFEST})")
    try:
        proj = load(root)
        locked = lock.read(proj.lock_path)
        if locked is None:
            raise ConfigError(f"no {lock.NAME} next to {MANIFEST}; run apply and commit it")
        if locked["scope"] != "project":
            raise ConfigError(f"{tilde(proj.lock_path)}: scope is {locked['scope']!r}, not 'project'")
        packs = proj.packs()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    notes: list[str] = []
    errors = compare_config({p.key: p.cfg for p in packs}, locked.get("packs", {}), MANIFEST)
    srcs = []
    if not errors:
        errors += planned(proj, locked)  # brainrc.toml's `harnesses`, checked from the lock alone
        for p in packs:
            found, src = _pack(p.key, p.cfg, p.root, locked["packs"][p.key],
                               lambda s: project_pack_files(proj, s), notes)
            errors += found
            srcs.append(src)
    if srcs and all(srcs) and not errors:  # every pack is here at its locked state: the lock's outputs too
        files, blocks = outputs(proj, srcs)
        errors += diff_outputs(locked, {r: lock.digest(d) for r, d in files.items()},
                               {r: lock.digest(b.encode("utf-8")) for r, b in blocks.items()})
    errors += _repo(proj.root, locked, proj.skill_tops)
    return _report(errors, notes, "Run `apply` to rewrite the files and relock, then commit both.")


def user() -> int:
    path = lock.user_lock_path()
    print(f"\nUser scope ({tilde(path)})")
    try:
        locked = lock.read(path)
        if locked is None:
            raise ConfigError(f"no {lock.NAME} at {tilde(path)}; run apply first")
        cfgs = {k: c for k, c in _layered("packs").items() if c.get("enabled", True)}
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    notes: list[str] = []
    errors = compare_config(cfgs, locked.get("packs", {}), "packs.toml")
    if not errors:
        for key, cfg in cfgs.items():
            errors += _pack(key, cfg, _pack_root(cfg, key), locked["packs"][key], lock.user_pack_files, notes)[0]
    return _report(errors, notes, "Run `apply` to relock, or `install --frozen` to restore the locked packs.")
