"""`brainrc migrate`: move the settings home (AICFG_HOME or ~/.config/ai-config) to the new one."""
from __future__ import annotations

import errno
import os
import shutil
import tempfile
from contextlib import ExitStack
from pathlib import Path

from . import config
from .config import tilde


def _source() -> Path:
    if os.environ.get("AICFG_HOME"):
        return config.expand(os.environ["AICFG_HOME"])
    return config._legacy_home()


# Names only brainrc writes into a settings home, plus the user's local files: a dir with none of
# these (and no rules/*.local.md) is not a settings home and is never moved. Generic names such as
# `rules`, `hooks` or `packs` alone don't count.
HOME_MARKERS = ("apply.lock", "extensions.md", "instructions.md", "packs.local.toml",
                "harnesses.local.toml", "mcp-owned.json", "active-run")


def _looks_like_home(source: Path) -> bool:
    return (any(os.path.lexists(source / m) for m in HOME_MARKERS)
            or any((source / "rules").glob("*.local.md")))


def _occupied(target: Path, ignore: Path | None = None) -> bool:
    """True if the target holds anything (a symlink counts); an empty dir, or one holding only
    `ignore`, doesn't."""
    if not os.path.lexists(target):
        return False
    if target.is_symlink() or not target.is_dir():
        return True
    return any(p != ignore for p in target.iterdir())


def _relative_env() -> str | None:
    for var in ("BRAINRC_HOME", "AICFG_HOME"):
        if os.environ.get(var) and not config.expand(os.environ[var]).is_absolute():
            return f"{var}={os.environ[var]} is a relative path; set an absolute one."
    return None


def _refusal(source: Path, target: Path) -> str | None:
    """Why this pair of paths must not be moved, or None."""
    src, tgt = Path(os.path.realpath(source)), Path(os.path.realpath(target))
    home = Path(os.path.realpath(Path.home()))
    if src == Path(src.anchor) or src == home or src in home.parents:
        return f"{tilde(source)} is /, your home directory or above it, not a settings home."
    if tgt == src or src in tgt.parents:
        return f"{tilde(target)} is inside {tilde(source)}."
    if not source.is_dir():
        return f"{tilde(source)} is not a directory."
    if not _looks_like_home(source):
        return (f"{tilde(source)} does not look like a settings home "
                f"(none of {', '.join(HOME_MARKERS)}, rules/*.local.md).")
    return None


def _move(source: Path, target: Path) -> OSError | None:
    """Put source at target: one rename, or across devices a copy beside the target renamed into
    place. Raises OSError while the target is not in place; returns the error if only removing the
    source failed."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():  # move the link, not what it points at, on any device
        link = config.readlink(source)
        if not os.path.isabs(link):
            link = os.path.normpath(os.path.join(source.parent, link))
        if target.is_dir() and not target.is_symlink():
            target.rmdir()  # empty, checked by the caller
        config.symlink(target, link)
        removed = source.unlink
    else:
        try:
            os.rename(source, target)
            return None
        except OSError as e:
            if e.errno != errno.EXDEV:
                raise
        tmp = Path(tempfile.mkdtemp(prefix=f".{target.name}.migrate-", dir=target.parent))
        try:
            os.chmod(tmp, os.stat(source).st_mode & 0o7777)
            shutil.copytree(source, tmp, symlinks=True, dirs_exist_ok=True)
            os.rename(tmp, target)
        except BaseException:
            shutil.rmtree(tmp, ignore_errors=True)
            raise
        removed = lambda: shutil.rmtree(source)
    try:
        removed()
    except OSError as e:
        return e
    return None


def _lock_all(stack: ExitStack, paths: list[Path]) -> Path | None:
    """Hold each lock file (once per file); returns the path of one another process holds, or None."""
    from . import cli
    seen = set()
    for lock in paths:
        lock.parent.mkdir(parents=True, exist_ok=True)
        f = stack.enter_context(open(lock, "a"))
        st = os.fstat(f.fileno())
        if (st.st_dev, st.st_ino) in seen:
            continue
        seen.add((st.st_dev, st.st_ino))
        if not cli._try_lock(f):
            return lock
    return None


def cmd_migrate(dry_run: bool) -> int:
    from . import cli  # cli imports this module
    if os.environ.get("AICFG_HOME") and not os.environ.get("BRAINRC_HOME"):
        print("ERROR AICFG_HOME is set and BRAINRC_HOME is not.")
        print("\nNothing moved. Set BRAINRC_HOME to the new location (or unset AICFG_HOME), then re-run.")
        return 1
    source, target = _source(), config.new_home()
    why = _relative_env()
    if why:
        print(f"ERROR {why}\n\nNothing moved.")
        return 1
    if not os.path.lexists(source) or config._same_dir(source, target):
        print(f"Nothing to migrate: no old settings home at {tilde(source)}.")
        return 0
    why = _refusal(source, target)
    if why:
        print(f"ERROR {why}")
        print("\nNothing moved.")
        return 1
    if _occupied(target, target / "apply.lock"):
        print(f"ERROR {tilde(target)} already exists and is not empty, so {tilde(source)} was not moved.")
        print("\nNothing moved. Merge or remove one of them by hand, then re-run.")
        return 1
    if dry_run:
        print(f"Would move {tilde(source)} -> {tilde(target)}, then run apply.")
        return 0
    # The locks apply takes: the source's, and the resolved home's (they differ when both env vars are set).
    locks = [source / "apply.lock"]
    if config.settings_home() / "apply.lock" not in locks:
        locks.append(config.settings_home() / "apply.lock")
    own = next((l for l in locks if l.parent == target), None)
    made_target = not os.path.lexists(target)
    leftover = None
    try:
        with ExitStack() as stack:
            busy = _lock_all(stack, locks)
            if busy:
                print(f"ERROR another brainrc apply is running (lock: {tilde(busy)})")
                print("\nNothing moved. Let it finish, then re-run.")
                return 1
            if os.name == "nt":
                # Windows won't rename or delete a dir with an open file in it, so let go of the
                # locks first. An apply that starts now holds its lock open, and the move fails safely.
                stack.close()
            if own:
                own.unlink(missing_ok=True)  # the target must be empty for the rename
            if _occupied(target):
                raise OSError(errno.ENOTEMPTY, "the target is no longer empty", str(target))
            leftover = _move(source, target)
    except OSError as e:
        if made_target and target.is_dir() and not target.is_symlink():
            try:
                target.rmdir()
            except OSError:
                pass
        print(f"ERROR {e}")
        print(f"\nNothing moved. {tilde(source)} is intact.")
        return 1
    if leftover:
        print(f"Copied {tilde(source)} -> {tilde(target)}; the copy is in place.")
        print(f"ERROR the old dir {tilde(source)} could not be fully removed: {leftover}")
        print("Remove what is left of it by hand.")
    else:
        print(f"Moved {tilde(source)} -> {tilde(target)}.")
    if cli.cmd_sync(apply=True) != 0:
        print(f"\nERROR the move is done, but apply failed. Fix the above, then run `{config.command('apply')}`.")
        return 1
    return 1 if leftover else 0
