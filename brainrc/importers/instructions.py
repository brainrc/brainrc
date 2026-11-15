"""CLAUDE.md and AGENTS.md (#163): one rule per section, in order.

A line that is only `@path` is a Claude Code import; its file's sections are imported in its place
(relative to the file that names it, `~` expanded, at most MAX_DEPTH deep), since rules must not
depend on one harness's syntax. A brainrc project block (`<!-- brainrc:begin ... -->`) is
brainrc's own output, so it is left out.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..config import expand, tilde
from ..project import BLOCK
from ..scaffold import Rule, slugify
from .markdown import split, to_rules
from .model import Imported

NAMES = ("CLAUDE.md", "AGENTS.md", "CLAUDE.local.md")
AT_IMPORT = re.compile(r"^@(\S+)\s*$")
MAX_DEPTH = 5


def detect(path: Path) -> bool:
    return path.is_file() and path.name in NAMES


def _segments(path: Path, out: Imported, depth: int = 0, chain: tuple[Path, ...] = ()) -> list[Rule]:
    """The file's rules, with each whole-line @import replaced by the imported file's rules."""
    label = tilde(path)
    out.read.add(path.resolve())
    text = BLOCK.sub(lambda m: "\n" * m[0].count("\n"), path.read_text(encoding="utf-8"))  # keep line numbers
    rules: list[Rule] = []
    lines = text.splitlines()
    start = 0

    def flush(end: int) -> None:
        part = "\n".join(lines[start:end])
        rules.extend(to_rules(split(part, start + 1), label, slugify(path.stem)))

    fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        m = AT_IMPORT.match(line) if not fence else None
        if not m:
            continue
        target = expand(m[1]) if m[1].startswith("~") else path.parent / m[1]
        target = target.resolve()
        if target in chain or target == path.resolve():
            out.warnings.append(f"{label}:{i + 1}: `{line.strip()}` imports itself; kept as text")
            continue
        if depth >= MAX_DEPTH or not target.is_file():
            why = "too deep" if depth >= MAX_DEPTH else "no such file"
            out.warnings.append(f"{label}:{i + 1}: `{line.strip()}` not inlined ({why}); kept as text")
            continue
        flush(i)
        rules += _segments(target, out, depth + 1, (*chain, path.resolve()))
        start = i + 1
    flush(len(lines))
    return rules


def read(path: Path) -> Imported:
    out = Imported()
    out.rules = _segments(path, out)
    if not out.rules:
        out.warnings.append(f"{tilde(path)}: no text to import")
    return out
