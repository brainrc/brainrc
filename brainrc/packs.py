"""Packs named by git URL: brainrc fetches them into $BRAINRC_HOME/packs/<key>."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from . import config
from .config import ConfigError, _layered
from .sources import _pack_root, check_subdir, clone_root, in_clone, subdir


def git_packs() -> list[tuple[str, dict, Path]]:
    """(key, config, pack root) for each enabled pack that names a `git` URL. The root is its clone,
    or the clone's `subdir` folder; the fetch functions here take that root and find the clone."""
    return [(key, cfg, _pack_root(cfg, key)) for key, cfg in _layered("packs").items()
            if "git" in cfg and cfg.get("enabled", True)]


def describe(key: str, cfg: dict, commit: str | None = None) -> str:
    """One `FETCH` line: the key, the URL, and the ref (or the remote's default branch), with the
    commit the lock pins it to when apply fetches that commit and not the ref."""
    pin = f", locked at {commit[:12]}" if commit else ""
    folder = f", folder {subdir(cfg)}" if subdir(cfg) else ""
    return f"{'FETCH':9} {key:9} {cfg['git']} ({cfg.get('ref', 'default branch')}{folder}{pin})"


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
    """On apply, once the clone matches, keep only a valid new-named record (no fetch needed).
    root is the pack's root, as for needs_fetch."""
    if needs_fetch(cfg, root):
        return
    root = clone_root(cfg, root)
    if _read_record(root / FETCHED) == _wanted(cfg) and not (root / OLD_FETCHED).exists():
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
    """Why the pack at root needs fetching for this config, or None when it matches. root is the
    pack's root: its clone, or the clone's `subdir` folder (sources.clone_root finds the clone)."""
    clone = clone_root(cfg, root)
    if not clone.exists():
        return "not fetched yet"
    was, want = fetched(clone), _wanted(cfg)
    if was is None:
        return "fetched before brainrc recorded its ref"
    for key in ("git", "ref"):
        if was.get(key) != want[key]:
            return f"fetched {key} `{was.get(key)}`, packs.toml says `{want[key]}`"
    try:
        check_subdir("", cfg, clone)
    except ConfigError as e:
        return str(e).split(": ", 1)[1]  # a folder that's missing or links out: refetching says which
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


def head(root: Path) -> str | None:
    """The commit a clone has checked out, or None. brainrc's clones are detached, so .git/HEAD
    holds it; anything else asks `git rev-parse HEAD` (local, no network)."""
    try:
        text = (root / ".git/HEAD").read_text().strip()
    except OSError:
        text = ""
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", text):
        return text
    try:
        return _git("rev-parse", "HEAD", cwd=root).strip() or None
    except (ConfigError, OSError):
        return None


def fetch_pack(key: str, cfg: dict, root: Path, commit: str | None = None, depth: int = 1) -> None:
    """Shallow-fetch the pack's ref, or the locked commit when one is given, and check it out,
    detached. A new clone is built beside its final place and moved in only when complete; an
    existing one is updated in place unless it has local changes. depth > 1 keeps that much
    history, so `update` can list the commits between the old pin and the new one. root is the
    pack's root; with a `subdir` the clone is the folder above it, checked to hold that folder."""
    root = clone_root(cfg, root)
    url, ref = str(cfg["git"]), str(cfg.get("ref", "HEAD"))
    if url.startswith("-") or ref.startswith("-"):
        raise ConfigError(f"pack {key}: `git` and `ref` can't start with '-'")
    want = commit or ref
    if root.exists():
        if _git("status", "--porcelain", cwd=root).strip():
            raise ConfigError(f"pack {key}: {root} has local changes; commit or discard them, then re-run")
        if not (commit and has_commit(root, commit)):
            _git("fetch", "-q", "--depth", str(depth), url, want, cwd=root)
        _has_folder(key, cfg, root, commit or "FETCH_HEAD")  # before checkout: a failure leaves it as it was
        _git("checkout", "-q", "--detach", commit or "FETCH_HEAD", cwd=root)
        _check_head(key, root, commit)
        check_subdir(key, cfg, root)
        _record(root, cfg)
        return
    tmp = root.with_name(f".{root.name}.fetching")
    config.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        _git("init", "-q", cwd=tmp)
        _git("fetch", "-q", "--depth", str(depth), url, want, cwd=tmp)
        _has_folder(key, cfg, tmp, "FETCH_HEAD")
        _git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=tmp)
        _check_head(key, tmp, commit)
        check_subdir(key, cfg, tmp)
        _record(tmp, cfg)
    except ConfigError:
        config.rmtree(tmp, ignore_errors=True)
        raise
    tmp.rename(root)


def _has_folder(key: str, cfg: dict, clone: Path, rev: str) -> None:
    """The pack's `subdir` is a folder (a tree, not a link) at rev, read without checking it out."""
    sub = subdir(cfg)
    if not sub:
        return
    try:
        kind = _git("cat-file", "-t", f"{rev}:{sub}", cwd=clone).strip()
    except ConfigError:
        kind = ""
    if not kind:
        raise ConfigError(f"pack {key}: no folder `{sub}` in {cfg['git']} at {cfg.get('ref', 'its default branch')}")
    if kind != "tree":
        raise ConfigError(f"pack {key}: `{sub}` in {cfg['git']} is a link or a file, not a folder")


def has_commit(root: Path, commit: str) -> bool:
    """True if the clone at root has this commit's objects (local, no network)."""
    try:
        _git("cat-file", "-e", f"{commit}^{{commit}}", cwd=root)
    except (ConfigError, OSError):
        return False
    return True


def _check_head(key: str, root: Path, commit: str | None) -> None:
    if commit and head(root) != commit:
        raise ConfigError(f"pack {key}: fetched {head(root)} for locked commit {commit}")


def pinned(locked: dict | None, key: str, cfg: dict) -> str | None:
    """The commit the lock pins this git pack to, or None: the lock must name the pack from the
    same URL and ref as the config, so changing `git` or `ref` (an intended move) unpins it."""
    entry = (locked or {}).get("packs", {}).get(key, {})
    if "commit" not in entry or "git" not in cfg:
        return None
    from .lock import clean_url  # lock imports this module
    if entry.get("git") != clean_url(str(cfg["git"])) or entry.get("ref") != str(cfg.get("ref", "HEAD")):
        return None
    return entry["commit"]


def to_fetch(cfg: dict, root: Path, pin: str | None) -> str | None:
    """Why apply fetches this git pack: its clone doesn't match the config, or isn't at the
    commit the lock pins. None when the clone is ready."""
    reason = needs_fetch(cfg, root)
    if reason or not pin:
        return reason
    at = head(clone_root(cfg, root))
    return None if at == pin else f"at {(at or '?')[:12]}, the lock pins {pin[:12]}"


UPDATE_DEPTH = 50  # commits of history `update` fetches, to list what moved


def commits_between(root: Path, old: str, new: str) -> list[str] | None:
    """`<short sha> <subject>` for each commit from old (excluded) to new that touches the pack
    (root: its folder, with a `subdir`), newest first, or None when old isn't an ancestor of new
    in the history fetched (a rewritten ref, or a longer gap)."""
    try:
        if old != new:
            _git("merge-base", "--is-ancestor", old, new, cwd=root)
        out = _git("log", "--format=%h %s", f"{old}..{new}", "--", ".", cwd=root)
    except (ConfigError, OSError):
        return None
    return [printable(line) for line in out.splitlines() if line]


def printable(text: str) -> str:
    """text with control characters (a terminal escape in a commit subject) shown as `?`."""
    return "".join(c if c.isprintable() else "?" for c in text)


def pinned_defaults(skip: str = "") -> list:
    """Core's default packs at the `git` and `ref` core's own packs.toml pins (packs.local.toml
    doesn't change them), for `validate --pack --fetch-defaults` (#139). Each is a clone of its own
    under $BRAINRC_HOME/validate-packs/, never the clone apply links, fetched only when it doesn't
    match. skip: the name of the pack being validated."""
    from .sources import _read_toml, default_packs, load_pack
    core = _read_toml(config.REPO / "packs.toml")
    found = []
    for key in default_packs():
        cfg = core[key]
        if "git" in cfg:
            tag = hashlib.sha256(f"{cfg['git']}\n{cfg.get('ref', 'HEAD')}".encode()).hexdigest()[:12]
            root = in_clone(cfg, config.settings_home() / "validate-packs" / f"{key}-{tag}")
            if needs_fetch(cfg, root):
                print(describe(key, cfg))
                if clone_root(cfg, root).exists():
                    config.rmtree(clone_root(cfg, root))
                fetch_pack(key, cfg, root)
        else:
            root = _pack_root(cfg, key)
        src = load_pack(root, key)
        if src.name != skip:
            found.append(src)
    return found
