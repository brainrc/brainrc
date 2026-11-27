"""Git's stand-ins for links (#120). With core.symlinks off, as on Windows without Developer Mode,
git checks out each symlink as a small plain file that holds the link's target. A pack whose skill
links elsewhere in the pack (Gatework's roles -> ../../agents) then has a file where a directory
should be. In copy mode apply copies what each stand-in points to, and validate reads a Markdown
link through one, so such a pack installs whole. Link mode leaves stand-ins as they are: a link to
the checkout would still find a plain file there."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

LINK = "120000"  # git's mode for a symlink
MAX_TARGET = 4096  # a stand-in holds one path; anything bigger is a real file
DRIVE = re.compile(r"^[A-Za-z]:")  # C:/... is absolute on Windows


def _top(directory: str) -> str | None:
    """The checkout that holds directory (the nearest folder with a .git), or None outside one."""
    here = Path(directory)
    for d in (here, *here.parents):
        if (d / ".git").exists():
            return str(d)
    return None


def _index(top: str) -> Path | None:
    """The checkout's index; in a worktree or a submodule .git is a file naming the git folder."""
    git = Path(top, ".git")
    if git.is_dir():
        return git / "index"
    try:
        line = git.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    if not line.startswith("gitdir:"):
        return None
    folder = Path(line[len("gitdir:"):].strip())
    return (folder if folder.is_absolute() else Path(top, folder)) / "index"


def _links(top: str) -> tuple[Path, ...]:
    """Every path git's index records as a link in one checkout, read once per index state."""
    index = _index(top)
    try:
        st = index.stat() if index else None
    except OSError:
        st = None
    if st is None:  # nothing to key a cache on: ask git each time
        return _read_links(top)
    return _cached_links(top, (st.st_mtime_ns, st.st_size))


def _read_links(top: str) -> tuple[Path, ...] | None:
    try:
        r = subprocess.run(["git", "-C", top, "ls-files", "-s", "-z"], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return tuple(Path(top, os.fsdecode(name)) for meta, _, name in
                 (e.partition(b"\t") for e in r.stdout.split(b"\0"))
                 if meta.startswith(LINK.encode()))


_cache: dict[tuple, tuple[Path, ...]] = {}


def _cached_links(top: str, stamp) -> tuple[Path, ...]:
    if (key := (top, stamp)) not in _cache:
        found = _read_links(top)
        if found is None:  # git failed: don't keep the answer
            return ()
        _cache[key] = found
    return _cache[key]


def _stand_ins(top: str) -> dict[Path, Path]:
    """{stand-in: what it points to} in one checkout: each path git records as a link that is a plain
    file here, whose target is relative, stays inside the checkout and exists."""
    found = {}
    for path in _links(top) or ():
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_TARGET:
                continue
            target = path.read_bytes().decode("utf-8").strip().replace("\\", "/")
        except (OSError, UnicodeDecodeError):
            continue
        if not target or target.startswith("/") or DRIVE.match(target):
            continue
        real = Path(os.path.normpath(path.parent / target))
        # inside the checkout, and not the stand-in's own folder or above it (a copy would hold itself)
        if real.exists() and real != path and real not in path.parents and Path(top) in real.parents:
            found[path] = real
    return found


def stand_ins(directory: Path) -> dict[Path, Path]:
    """Git's stand-ins at or under directory (a path inside a checkout), with what each points to."""
    top = _top(os.path.realpath(directory if Path(directory).is_dir() else Path(directory).parent))
    if top is None:
        return {}
    base = Path(os.path.realpath(directory))
    return {p: t for p, t in _stand_ins(top).items() if p == base or base in p.parents}


def resolve(path: Path) -> Path:
    """path read through any stand-in on its way: roles/brainrc-analyst.md under a roles stand-in for
    ../../agents is agents/brainrc-analyst.md. Returns path itself when none is on its way."""
    path = Path(os.path.abspath(path))
    for _ in range(8):  # a stand-in may point through another
        parent = path.parent
        while not parent.is_dir() and parent != parent.parent:
            parent = parent.parent
        top = _top(os.path.realpath(parent))
        if top is None:
            return path
        here = Path(os.path.realpath(parent)) / path.relative_to(parent)
        hit = next(((p, t) for p, t in _stand_ins(top).items()
                    if p == here or p in here.parents), None)
        if hit is None:
            return path
        path = hit[1] / here.relative_to(hit[0])
    return path
