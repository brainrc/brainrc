"""Packs named by git URL: brainrc fetches them into $BRAINRC_HOME/packs/<key>."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .config import ConfigError, _layered
from .sources import _pack_root


def git_packs() -> list[tuple[str, dict, Path]]:
    """(key, config, clone dir) for each enabled pack that names a `git` URL."""
    return [(key, cfg, _pack_root(cfg, key)) for key, cfg in _layered("packs").items()
            if "git" in cfg and cfg.get("enabled", True)]


def describe(key: str, cfg: dict) -> str:
    """One `FETCH` line: the key, the URL, and the ref (or the remote's default branch)."""
    return f"{'FETCH':9} {key:9} {cfg['git']} ({cfg.get('ref', 'default branch')})"


FETCHED = ".git/brainrc-fetched.json"  # inside .git: invisible to `git status` and the pack's items
OLD_FETCHED = ".git/aicfg-fetched.json"  # read when FETCHED is absent or unreadable; removed on apply


def _wanted(cfg: dict) -> dict:
    return {"git": str(cfg["git"]), "ref": str(cfg.get("ref", "HEAD"))}


def _read_record(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def fetched(root: Path) -> dict | None:
    """The `git` and `ref` the clone at root was last fetched from, or None if not recorded."""
    return _read_record(root / FETCHED) or _read_record(root / OLD_FETCHED)


def adopt_record(cfg: dict, root: Path) -> None:
    """On apply, once the clone matches, keep only a valid new-named record (no fetch needed)."""
    if needs_fetch(cfg, root) or (_read_record(root / FETCHED) == _wanted(cfg)
                                  and not (root / OLD_FETCHED).exists()):
        return
    try:
        _record(root, cfg)
    except OSError:
        pass  # a read-only clone still works from the record it has


def _record(root: Path, cfg: dict) -> None:
    """Write the fetch record, then drop the old-named one."""
    (root / FETCHED).write_text(json.dumps(_wanted(cfg)) + "\n")
    (root / OLD_FETCHED).unlink(missing_ok=True)


def needs_fetch(cfg: dict, root: Path) -> str | None:
    """Why the clone at root needs fetching for this config, or None when it matches."""
    if not root.exists():
        return "not fetched yet"
    was, want = fetched(root), _wanted(cfg)
    if was is None:
        return "fetched before brainrc recorded its ref"
    for key in ("git", "ref"):
        if was.get(key) != want[key]:
            return f"fetched {key} `{was.get(key)}`, packs.toml says `{want[key]}`"
    return None


GIT_TIMEOUT = 60  # seconds; an unreachable host or a credential prompt must not hang apply


def _git(*args: str, cwd: Path) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ConfigError(f"git {args[0]} timed out after {GIT_TIMEOUT}s") from None
    if result.returncode:
        detail = (result.stderr.strip().splitlines() or [f"exit {result.returncode}"])[-1]
        raise ConfigError(f"git {args[0]} failed: {detail}")
    return result.stdout


def fetch_pack(key: str, cfg: dict, root: Path) -> None:
    """Shallow-fetch the pack's ref and check it out, detached. A new clone is built beside its
    final place and moved in only when complete; an existing one is updated in place unless it
    has local changes."""
    url, ref = str(cfg["git"]), str(cfg.get("ref", "HEAD"))
    if url.startswith("-") or ref.startswith("-"):
        raise ConfigError(f"pack {key}: `git` and `ref` can't start with '-'")
    if root.exists():
        if _git("status", "--porcelain", cwd=root).strip():
            raise ConfigError(f"pack {key}: {root} has local changes; commit or discard them, then update")
        _git("fetch", "-q", "--depth", "1", url, ref, cwd=root)
        _git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=root)
        _record(root, cfg)
        return
    tmp = root.with_name(f".{root.name}.fetching")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        _git("init", "-q", cwd=tmp)
        _git("fetch", "-q", "--depth", "1", url, ref, cwd=tmp)
        _git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=tmp)
        _record(tmp, cfg)
    except ConfigError:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    tmp.rename(root)
