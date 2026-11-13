"""Helpers the tests share so they run the same on Windows as on macOS and Linux (#342)."""
import os
import shutil
import stat
import sys

# Path.home() reads USERPROFILE on Windows and HOME elsewhere, so a fake home sets both.
HOME_KEYS = ("HOME", "USERPROFILE")


def home_env(path) -> dict[str, str]:
    """The environment entries that make `path` the home directory, for os.environ or a child."""
    return {k: str(path) for k in HOME_KEYS}


def saved_home() -> dict[str, str | None]:
    """The current home variables, for restore_home()."""
    return {k: os.environ.get(k) for k in HOME_KEYS}


def restore_home(old: dict[str, str | None]) -> None:
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _writable_retry(func, path, _exc):
    """Git marks its object files read-only, and Windows won't delete a read-only file."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def rmtree(path, ignore_errors: bool = False) -> None:
    """shutil.rmtree that also removes read-only files (a git checkout's objects on Windows)."""
    handler = {"onexc" if sys.version_info >= (3, 12) else "onerror": _writable_retry}
    try:
        shutil.rmtree(path, **handler)
    except OSError:
        if not ignore_errors:
            raise


def bare_env(home, **extra: str) -> dict[str, str]:
    """A near-empty child environment with `home` as its home. Windows can't start a process
    without SYSTEMROOT, so that one is kept when set."""
    keep = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT") if k in os.environ}
    return {**keep, **home_env(home), **extra}
