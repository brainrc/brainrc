"""CLAUDE.md and AGENTS.md (#163): one rule per section, in order.

A line that is only `@path` is a Claude Code import; that file's text takes its place (relative to
the file that names it, `~` expanded, at most MAX_DEPTH deep) before the text is split, since rules
must not depend on one harness's syntax. A brainrc project block (`<!-- brainrc:begin ... -->`) is
brainrc's own output, so it is left out.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..config import expand, tilde
from ..project import BLOCK
from ..scaffold import slugify
from .markdown import fenced, rules_from_lines
from .model import Imported

NAMES = ("CLAUDE.md", "AGENTS.md", "CLAUDE.local.md")
LOOK_FOR = ("CLAUDE.md", "AGENTS.md")  # in a folder: not CLAUDE.local.md, which is personal
AT_IMPORT = re.compile(r"^@(\S+)\s*$")
MAX_DEPTH = 5


def detect(path: Path) -> bool:
    return path.is_file() and path.name in NAMES


def _lines(path: Path, out: Imported, depth: int = 0, chain: tuple[Path, ...] = ()) -> list[tuple[str, int, str]]:
    """(label, line number, text) for the file, each whole-line @import replaced by its file's lines."""
    label = tilde(path)
    me = path.resolve()
    out.read.add(me)
    text = BLOCK.sub(lambda m: "\n" * m[0].count("\n"), path.read_text(encoding="utf-8-sig"))  # keep line numbers
    lines = text.splitlines()
    result = []
    for i, (line, in_fence) in enumerate(zip(lines, fenced(lines))):
        m = None if in_fence else AT_IMPORT.match(line)
        if m:
            target = (expand(m[1]) if m[1].startswith("~") else path.parent / m[1]).resolve()
            why = ("imports itself" if target in (*chain, me) else "too deep" if depth >= MAX_DEPTH
                   else "no such file" if not target.is_file() else "")
            if not why:
                result += _lines(target, out, depth + 1, (*chain, me))
                continue
            out.warnings.append(f"{label}:{i + 1}: `{line.strip()}` not inlined ({why}); kept as text")
        result.append((label, i + 1, line))
    return result


def read(path: Path) -> Imported:
    out = Imported()
    out.rules = rules_from_lines(_lines(path, out), slugify(path.stem))
    if not out.rules:
        out.warnings.append(f"{tilde(path)}: no text to import")
    return out
