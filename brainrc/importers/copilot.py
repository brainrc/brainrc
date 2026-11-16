"""GitHub Copilot instructions (#165): `.github/copilot-instructions.md`, and the path-specific
`.github/instructions/**/*.instructions.md`.

copilot-instructions.md applies to every request, so it becomes rules, one per section, in order.
A path-specific file with `applyTo: "**"` applies everywhere too and becomes one rule; one scoped
to other globs becomes a skill with a row in Gatework's Domains table for them, as Cursor's do.
"""
from __future__ import annotations

from pathlib import Path

from ..config import tilde
from ..scaffold import Rule, slugify
from .markdown import globs, split, to_rules, whole_body
from .model import Imported

NAMES = ("copilot-instructions.md",)
LOOK_FOR = (".github/copilot-instructions.md", ".github/instructions")
SUFFIX = ".instructions.md"
EVERYWHERE = ("**", "**/*")  # `*` is the root folder only


def detect(path: Path) -> bool:
    if path.is_file():
        return path.name in NAMES or path.name.endswith(SUFFIX)
    return path.is_dir() and path.name == "instructions" and path.parent.name == ".github"


def _path_specific(path: Path, root: Path, label: str, out: Imported) -> None:
    whole = whole_body(path.read_text(encoding="utf-8-sig"))
    if not whole:
        out.warnings.append(f"{label}: no text to import")
        return
    meta, body, first, last = whole
    provenance = f"imported by brainrc from {label}, lines {first}-{last}"
    name = path.relative_to(root).as_posix()[:-len(SUFFIX)].replace("/", "-")
    slug = out.unique(slugify(name, "instructions"))
    if "coding-agent" in globs(meta.get("excludeAgent", "")):
        out.warnings.append(f"{label}: only for Copilot code review (excludeAgent: coding-agent); skipped")
        return
    scoped = globs(meta.get("applyTo", ""))
    if any(g in EVERYWHERE for g in scoped):  # one glob for every file covers them all
        out.rules.append(Rule(slug, body, provenance))
        return
    out.add_skill(slug, " ".join(meta.get("description", "").split()), scoped, body, provenance, label,
                  f"Copilot instructions `{path.name}`; use when asked to apply them.", "description or applyTo")


def read(path: Path) -> Imported:
    out = Imported()
    if path.is_file() and not path.name.endswith(SUFFIX):  # repo-wide, like copilot-instructions.md
        out.read.add(path.resolve())
        out.rules += to_rules(split(path.read_text(encoding="utf-8-sig")), tilde(path), "copilot")
        if not out.rules:
            out.warnings.append(f"{tilde(path)}: no text to import")
        return out
    root = path if path.is_dir() else path.parent
    for f in out.files(path, SUFFIX):
        _path_specific(f, root, tilde(f), out)
    return out
