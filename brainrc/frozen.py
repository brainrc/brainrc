"""`install --frozen` (#284): install exactly what brainrc.lock records, or fail and write nothing.

Every check runs before anything is written: the config and the lock name the same packs from the
same places, each git pack's locked commit is fetched (never its ref) into a temporary clone, and
every installed file hashes as the lock says. Only then do the clones move into place and the
files get written. The lock itself is never rewritten here.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from . import lock
from .config import ConfigError, _layered, tilde
from .packs import _git, _record, head
from .project import (
    MANIFEST, Project, _linked, _read, _unit, foreign, load, outputs, planned, project_pack_files, remember,
    with_block,
)
from .sources import _pack_root, core_version, load_pack


def _version_note(locked: dict) -> None:
    mine = ".".join(map(str, core_version()))
    if locked["brainrc"] != mine:
        print(f"WARN the lock was written by brainrc {locked['brainrc']}; this is {mine}")


def compare_config(cfgs: dict[str, dict], locked: dict[str, dict], where: str) -> list[str]:
    """Each way the config's enabled packs differ from the lock's: a pack only in one of them, or
    another origin (git URL, ref, path)."""
    errors = [f"pack {k}: in {where} but not in {lock.NAME} (run apply to relock)" for k in cfgs if k not in locked]
    errors += [f"pack {k}: in {lock.NAME} but not enabled in {where}" for k in locked if k not in cfgs]
    for key in (k for k in cfgs if k in locked):
        cfg, entry = cfgs[key], locked[key]
        if ("git" in cfg) != ("git" in entry):
            kinds = ("git" if "git" in cfg else "path", "git" if "git" in entry else "path")
            errors.append(f"pack {key}: {where} names it by `{kinds[0]}`, {lock.NAME} by `{kinds[1]}`")
            continue
        wanted = {"git": lock.clean_url(str(cfg["git"])), "ref": str(cfg.get("ref", "HEAD"))} if "git" in cfg \
            else {"path": lock.shown_path(str(cfg["path"]))}
        for k, v in wanted.items():
            if entry[k] != v:
                errors.append(f"pack {key}: `{k}` is {v!r} in {where} but {entry[k]!r} in {lock.NAME} (run apply to relock)")
    return errors


def diff_files(key: str, want: dict[str, str], got: dict[str, str]) -> list[str]:
    errors = []
    for rel in sorted(set(want) | set(got)):
        if rel not in got:
            errors.append(f"pack {key}: {rel} is in {lock.NAME} but not in the pack")
        elif rel not in want:
            errors.append(f"pack {key}: {rel} is in the pack but not in {lock.NAME}")
        elif want[rel] != got[rel]:
            errors.append(f"pack {key}: {rel} differs from {lock.NAME}")
    return errors


class Stage:
    """Temporary clones of locked commits, moved into place only when every check passed."""

    def __init__(self):
        self.moves: list[tuple[Path, Path]] = []  # (temporary clone, final place)

    def clone(self, key: str, cfg: dict, entry: dict, final: Path) -> Path:
        """A directory holding the pack at its locked commit: the existing clone when it is already
        there, else a fresh one beside it. Raises ConfigError naming the commit."""
        commit, url = entry["commit"], str(cfg["git"])
        if url.startswith("-"):
            raise ConfigError(f"pack {key}: `git` can't start with '-'")
        if final.is_dir() and head(final) == commit and not _git("status", "--porcelain", cwd=final).strip():
            return final
        tmp = final.with_name(f".{final.name}.frozen-{os.getpid()}")
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        self.moves.append((tmp, final))
        try:
            _git("init", "-q", cwd=tmp)
            _git("fetch", "-q", "--depth", "1", url, commit, cwd=tmp)
            _git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=tmp)
        except ConfigError as e:
            raise ConfigError(f"pack {key}: locked commit {commit[:12]} can't be fetched from {entry['git']} ({e})") from None
        if head(tmp) != commit:
            raise ConfigError(f"pack {key}: fetched {head(tmp)} for locked commit {commit}")
        _record(tmp, cfg)  # its git and ref, so apply and status see a clone that matches the config
        return tmp

    def discard(self) -> None:
        for tmp, _ in self.moves:
            shutil.rmtree(tmp, ignore_errors=True)

    def commit(self) -> None:
        for tmp, final in self.moves:
            old = final.with_name(f".{final.name}.old-{os.getpid()}")
            shutil.rmtree(old, ignore_errors=True)
            if final.exists():
                final.rename(old)
            tmp.rename(final)
            shutil.rmtree(old, ignore_errors=True)


def _fail(errors: list[str], stage: Stage, what: str) -> int:
    stage.discard()
    for e in errors:
        print(f"ERROR {e}")
    print(f"\nNothing written. {what}")
    return 1


def check_packs(cfgs: dict[str, dict], roots: dict[str, Path], locked: dict, where: str, files_of,
                stage: Stage) -> tuple[list[str], dict]:
    """(errors, sources by key) for the frozen packs; files_of(src) gives a pack's installed files."""
    errors = compare_config(cfgs, locked.get("packs", {}), where)
    srcs = {}
    if errors:
        return errors, srcs
    for key, cfg in cfgs.items():
        entry = locked["packs"][key]
        try:
            root = stage.clone(key, cfg, entry, roots[key]) if "git" in cfg else roots[key]
            if not root.is_dir():
                raise ConfigError(f"pack {key}: no directory at {tilde(root)}")
            srcs[key] = load_pack(root, key)
        except ConfigError as e:
            errors.append(str(e))
            continue
        errors += diff_files(key, entry["files"], files_of(srcs[key]))
    return errors, srcs


def user(sync) -> int:
    """The user scope from $BRAINRC_HOME/brainrc.lock; sync(apply) then links what it installed."""
    path = lock.user_lock_path()
    stage = Stage()
    try:
        locked = lock.read(path)
        if locked is None:
            raise ConfigError(f"no {lock.NAME} at {tilde(path)}; run apply first")
        cfgs = {k: c for k, c in _layered("packs").items() if c.get("enabled", True)}
        roots = {k: _pack_root(c, k) for k, c in cfgs.items()}
    except ConfigError as e:
        return _fail([str(e)], stage, "Fix it, then re-run.")
    _version_note(locked)
    errors, _ = check_packs(cfgs, roots, locked, "packs.toml", lock.user_pack_files, stage)
    if errors:
        return _fail(errors, stage, f"Run `apply` to install the current packs and relock, or restore {lock.NAME}.")
    stage.commit()
    return sync()


def project(root: Path, force: bool = False) -> int:
    """The project at root from its brainrc.lock: its packs' files, written into the repo. A file
    at one of the lock's paths that brainrc didn't write fails it, unless force."""
    print(f"\nProject {tilde(root)} ({MANIFEST})")
    stage = Stage()
    try:
        proj = load(root)
        locked = lock.read(proj.lock_path)
        if locked is None:
            raise ConfigError(f"no {lock.NAME} next to {MANIFEST}; run apply first")
        if locked["scope"] != "project":
            raise ConfigError(f"{tilde(proj.lock_path)}: scope is {locked['scope']!r}, not 'project'")
        packs = proj.packs()
    except ConfigError as e:
        return _fail([str(e)], stage, "Fix it, then re-run.")
    _version_note(locked)
    cfgs = {p.key: p.cfg for p in packs}
    roots = {p.key: p.root for p in packs}
    errors, srcs = check_packs(cfgs, roots, locked, MANIFEST, lambda s: project_pack_files(proj, s), stage)
    files: dict[str, bytes] = {}
    blocks: dict[str, str] = {}
    if not errors:
        errors += planned(proj, locked)  # brainrc.toml's `harnesses` moved files the lock put elsewhere
    if not errors:
        files, blocks = outputs(proj, [srcs[p.key] for p in packs])
        errors += diff_outputs(locked, {r: lock.digest(d) for r, d in files.items()},
                               {r: lock.digest(b.encode("utf-8")) for r, b in blocks.items()})
        errors += [f"{rel}: a directory on its way is a link; brainrc won't write through it"
                   for rel in sorted({*files, *blocks}) if _linked(proj.root, rel)]
        errors += [f"{rel}: is a link; brainrc won't write through it" for rel in sorted(blocks)
                   if (proj.root / rel).is_symlink()]
    if errors:
        return _fail(errors, stage, f"Run `apply` to install the current packs and relock, or restore {lock.NAME}.")
    if not force:
        errors = foreign(proj.root, locked, files, blocks)
        if errors:
            return _fail(errors, stage, "Move or commit those files, or pass --force to overwrite them.")
    stage.commit()
    _write_frozen(proj, files, blocks)
    remember(proj.root, locked.get("outputs", {}), locked.get("blocks", {}))
    return 0


def diff_outputs(locked: dict, files: dict[str, str], blocks: dict[str, str]) -> list[str]:
    errors = []
    for table, got in (("outputs", files), ("blocks", blocks)):
        want = locked.get(table, {})
        for rel in sorted(set(want) | set(got)):
            if want.get(rel) != got.get(rel):
                errors.append(f"{rel}: the packs at their locked state don't produce what {lock.NAME} records "
                              f"({'missing from the lock' if rel not in want else 'not produced' if rel not in got else 'differs'})")
    return errors


def _write_frozen(proj: Project, files: dict[str, bytes], blocks: dict[str, str]) -> None:
    """Build every changed file in a temporary directory in the repo, then move each into place."""
    changes: dict[str, bytes] = {rel: data for rel, data in files.items() if _read(proj.root / rel) != data}
    for rel, block in blocks.items():
        path = proj.root / rel
        current = path.read_bytes().decode("utf-8") if path.is_file() else None
        new = with_block(current, block)
        if new != current:
            changes[rel] = new.encode("utf-8")
    tops = proj.skill_tops
    tmp = proj.root / f".brainrc-install-{os.getpid()}"
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        for n, (rel, data) in enumerate(sorted(changes.items())):
            (tmp / str(n)).parent.mkdir(parents=True, exist_ok=True)
            (tmp / str(n)).write_bytes(data)
        states: dict[str, str] = {}
        for n, rel in enumerate(sorted(changes)):
            dest = proj.root / rel
            state = "update" if dest.exists() else "create"
            states[_unit(rel, tops)] = "update" if states.get(_unit(rel, tops)) == "update" else state
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(tmp / str(n), dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for unit, state in sorted(states.items()):
        print(f"{state.upper():9} {'project':9} {unit}")
    print(f"Project installed from {lock.NAME}." if states else "Project in sync with its lock.")

