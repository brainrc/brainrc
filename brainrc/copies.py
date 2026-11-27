"""Copy mode (#177): managed copies where a symlink can't be made.

Native Windows makes a symlink only with Developer Mode or as an administrator. There apply copies
each item it would link (a skill directory, an agent, the rules file, a hooks dir, a plugin) and
records the copy in the settings home's copies.json: where it came from, a digest of the source
when it was copied, and a digest of what was written. Status, doctor and uninstall read the record,
so a managed copy is treated like a managed link: refreshed when its source changes, pruned when
nothing installs it any more, removed by uninstall. A copy whose digest no longer matches the
record was edited by hand, and is reported, never overwritten.

The mode is brainrc.local.toml's `link_mode`: "auto" (the default) links on macOS and Linux and on
a Windows machine that allows symlinks, and copies on one that doesn't; "symlink" or "copy" sets it.
BRAINRC_LINK_MODE overrides the file for one run (CI, tests).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from . import config, gitlinks
from .config import ConfigError, tilde

MODES = ("auto", "symlink", "copy")
RECORD = "copies.json"
ENV = "BRAINRC_LINK_MODE"
_probed: dict[str, bool] = {}


def _stamp(path: Path):
    try:
        st = path.stat()
    except OSError:
        return None
    return st.st_mtime_ns, st.st_size, st.st_ino


_cache: dict[str, tuple] = {}  # "mode" and "record": (path, stamp, value), so a run reads each once


def configured() -> str:
    """The mode asked for: $BRAINRC_LINK_MODE, else brainrc.local.toml's `link_mode`, else auto."""
    if os.environ.get(ENV):
        mode = os.environ[ENV]
        if mode not in MODES:
            raise ConfigError(f"{ENV}={mode!r}: must be one of {', '.join(MODES)}")
        return mode
    path = config.local_dir() / config.PROFILE_FILE
    stamp = _stamp(path)
    if _cache.get("mode", (None, None))[:2] == (path, stamp) and stamp is not None:
        return _cache["mode"][2]
    data = config._read_toml(path)
    mode = data.get("link_mode", "auto")
    if mode not in MODES:
        raise ConfigError(f"{tilde(path)}:{config.line_of(path.read_text(), 'link_mode')}: `link_mode` must be "
                          f"one of {', '.join(MODES)}")
    _cache["mode"] = (path, stamp, mode)
    return mode


def can_symlink() -> bool:
    """True when this process can make a symlink (always on POSIX; on Windows, with Developer Mode
    or as an administrator). Tried once per run, in a temporary directory."""
    if os.name != "nt":
        return True
    if "ok" not in _probed:
        d = tempfile.mkdtemp(prefix="brainrc-link-")
        try:
            os.symlink(d, os.path.join(d, "probe"), target_is_directory=True)
            _probed["ok"] = True
        except OSError:
            _probed["ok"] = False
        finally:
            config.rmtree(d, ignore_errors=True)
    return _probed["ok"]


def mode() -> str:
    """"symlink" or "copy": how apply installs items on this machine now."""
    asked = configured()
    if asked == "auto":
        return "symlink" if can_symlink() else "copy"
    return asked


def copying() -> bool:
    return mode() == "copy"


def record_path() -> Path:
    return config.settings_home() / RECORD


def read() -> dict[str, dict]:
    """{dest: {"harness", "source", "source_digest", "digest"}} for every copy apply recorded."""
    path = record_path()
    stamp = _stamp(path)
    if stamp is None:
        return {}
    if _cache.get("record", (None, None))[:2] == (path, stamp):
        return dict(_cache["record"][2])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    copies = data.get("copies") if isinstance(data, dict) else None
    record = {k: v for k, v in copies.items() if isinstance(v, dict)} if isinstance(copies, dict) else {}
    _cache["record"] = (path, stamp, record)
    return dict(record)


def _write(record: dict[str, dict]) -> None:
    path = record_path()
    if not record:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.brainrc-tmp-{os.getpid()}")
    tmp.write_text(json.dumps({"version": 1, "copies": dict(sorted(record.items()))}, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)
    _cache.pop("record", None)


def key(dest: Path) -> str:
    return str(Path(os.path.abspath(dest)))


def recorded(dest: Path) -> dict | None:
    return read().get(key(dest))


def digest(path: Path, _seen: frozenset = frozenset()) -> str | None:
    """sha256 of a file, or of a directory's files (each path under it and its bytes), links and
    git's stand-ins for links followed; None when nothing is there. __pycache__ and .pyc files don't
    count."""
    if path.is_file():
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if not path.is_dir():
        return None
    h = hashlib.sha256()
    for rel, p in _tree(path):
        h.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    for stand_in, target in sorted(gitlinks.stand_ins(path).items()):  # what a copy puts in its place
        inner = "loop" if target in _seen else digest(target, _seen | {target}) or ""
        h.update(b"stand-in\0" + stand_in.relative_to(path).as_posix().encode("utf-8") + b"\0" + inner.encode())
    return "sha256:" + h.hexdigest()


def edited(dest: Path, entry: dict) -> bool:
    """True when the copy at dest no longer holds what apply wrote (missing doesn't count)."""
    return os.path.lexists(dest) and not dest.is_symlink() and digest(dest) != entry.get("digest")


def current(dest: Path, source: Path, entry: dict) -> bool:
    """True when the recorded copy at dest is of source as it is now."""
    return (os.path.normpath(entry.get("source", "")) == os.path.normpath(source)
            and entry.get("source_digest") == digest(source))


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        config.rmtree(path)
    else:
        path.unlink()


def remove(dest: Path) -> None:
    """Delete a managed copy (or link) at dest and its record."""
    if os.path.lexists(dest):
        _remove_path(dest)
    forget(dest)


def forget(dest: Path) -> None:
    record = read()
    if record.pop(key(dest), None) is not None:
        _write(record)


def place(harness: str, dest: Path, source: Path, render=None) -> None:
    """Install source at dest in this machine's mode, replacing brainrc's own link or copy there.
    render(text, source) -> text rewrites each copied text file so it works where it sits (a hook or
    plugin that finds the guards from its own path); the copy is built beside dest first, so a
    failure leaves what was there."""
    if not copying():
        if os.path.lexists(dest):
            _remove_path(dest)
        forget(dest)
        config.symlink(dest, source)
        return
    real = Path(os.path.realpath(source))
    tmp = dest.with_name(f".{dest.name}.brainrc-tmp-{os.getpid()}")
    if os.path.lexists(tmp):
        _remove_path(tmp)
    try:
        if real.is_dir():
            shutil.copytree(real, tmp, ignore=_skipped)
            follow = gitlinks.resolve if _copy_stand_ins(real, tmp) else Path
            files = [(tmp / rel, follow(Path(source) / rel)) for rel, _ in _tree(tmp)]
        else:
            shutil.copyfile(real, tmp)
            files = [(tmp, Path(source))]
        for path, src in files if render is not None else ():
            try:
                text = path.read_bytes().decode("utf-8")  # bytes, so a CRLF file keeps its line ends
            except UnicodeDecodeError:
                continue
            if (new := render(text, src)) != text:
                path.write_bytes(new.encode("utf-8"))
        if os.path.lexists(dest):
            _remove_path(dest)
        os.replace(tmp, dest)
    except BaseException:
        if os.path.lexists(tmp):
            _remove_path(tmp)
        raise
    record = read()
    record[key(dest)] = {"harness": harness, "source": str(source), "source_digest": digest(source),
                         "digest": digest(dest)}
    _write(record)


def _copy_stand_ins(real: Path, tmp: Path, _seen: frozenset = frozenset()) -> bool:
    """Replace each of git's stand-ins for a link (a checkout without symlinks) in the copy with a
    copy of what it points to, as a link mode would show it (brainrc/gitlinks.py). True if any."""
    found = gitlinks.stand_ins(real)
    for stand_in, target in sorted(found.items()):
        if target in _seen:
            raise ConfigError(f"{tilde(stand_in)}: git's stand-ins for links point at each other; "
                              "a copy can't hold that loop (link_mode = \"symlink\" can)")
        at = tmp / stand_in.relative_to(real)
        at.unlink()
        if target.is_dir():
            shutil.copytree(target, at, ignore=_skipped)
            _copy_stand_ins(target, at, _seen | {target})
        else:
            shutil.copyfile(target, at)
    return bool(found)


def _skipped(directory: str, names: list[str]) -> set[str]:
    """What a copy leaves out: bytecode, and a link to nothing (a link mode leaves it dangling; a copy
    can't hold it). Not copytree's ignore_dangling_symlinks, which reads a relative link's target
    from the working directory, so it drops a good one like Gatework's roles -> ../../agents."""
    return {n for n in names if n == "__pycache__" or n.endswith(".pyc")
            or not os.path.exists(os.path.join(directory, n))}


def _tree(path: Path):
    from .sources import tree_files
    return tree_files(path)


def stale(wanted: set[Path], in_scope) -> tuple[list[Path], list[Path]]:
    """Recorded copies apply no longer makes, in scope: (unedited ones to prune, edited ones it
    leaves). A copy already deleted by hand is neither; apply drops it from the record."""
    prune, kept = [], []
    wanted = {key(d) for d in wanted}
    for dest, entry in sorted(read().items()):
        p = Path(dest)
        if key(p) in wanted or not in_scope(entry.get("harness", "")) or not os.path.lexists(p) or p.is_symlink():
            continue
        (kept if edited(p, entry) else prune).append(p)
    return prune, kept


def tidy(in_scope) -> None:
    """Drop records of copies that are gone (deleted by hand, or replaced by a link of the user's)."""
    record = read()
    keep = {k: v for k, v in record.items()
            if not in_scope(v.get("harness", "")) or (os.path.lexists(k) and not Path(k).is_symlink())}
    if keep != record:
        _write(keep)
