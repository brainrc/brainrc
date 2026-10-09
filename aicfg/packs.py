"""Packs named by git URL: aicfg fetches them into $AICFG_HOME/packs/<key>."""
from __future__ import annotations

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


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
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
        return
    tmp = root.with_name(f".{root.name}.fetching")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        _git("init", "-q", cwd=tmp)
        _git("fetch", "-q", "--depth", "1", url, ref, cwd=tmp)
        _git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=tmp)
    except ConfigError:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    tmp.rename(root)
