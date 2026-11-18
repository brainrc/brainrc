"""Windsurf rules (#166): `.windsurfrules`, `global_rules.md`, and `.windsurf/rules/**/*.md`.

`.windsurfrules` (the older workspace file) and `global_rules.md` (Windsurf's global rules) apply
to every request, so they become rules, one per section, in order. A file in `.windsurf/rules/`
is kept whole and maps by its `trigger`: `always_on` becomes a rule; `glob` a skill with a row in
Gatework's Domains table for its `globs`, as Cursor's scoped rules do; `model_decision` a skill
with its `description`; `manual`, or no trigger, a skill the model loads only when asked, with a
warning. Files are read in path order, which is Windsurf's order.
"""
from __future__ import annotations

from pathlib import Path

from ..config import tilde
from ..scaffold import Rule, slugify
from .markdown import globs, split, to_rules, whole_body
from .model import Imported

NAMES = (".windsurfrules", "global_rules.md")
LOOK_FOR = (".windsurf/rules", ".windsurfrules")
TRIGGERS = ("always_on", "glob", "model_decision", "manual")


def detect(path: Path) -> bool:
    if path.is_file():
        return path.name in NAMES or (path.suffix == ".md" and _in_rules(path))
    return path.is_dir() and path.name == "rules" and path.parent.name == ".windsurf"


def _in_rules(path: Path) -> bool:
    return any(p.name == "rules" and p.parent.name == ".windsurf" for p in path.parents)


def _slug(path: Path, root: Path) -> str:
    """`backend/10-api.md` -> `backend-api`: the path, without the ordering numbers."""
    parts = [p.lstrip("0123456789-_") or p for p in (*path.relative_to(root).parent.parts, path.stem)]
    return slugify("-".join(parts), "rule")


def _rule_file(path: Path, slug: str, label: str, out: Imported) -> None:
    whole = whole_body(path.read_text(encoding="utf-8-sig"))
    if not whole:
        out.warnings.append(f"{label}: no text to import")
        return
    meta, body, first, last = whole  # kept whole: Windsurf loads the file as one rule
    provenance = f"imported by brainrc from {label}, lines {first}-{last}"
    trigger = meta.get("trigger", "").strip().lower()
    if trigger and trigger not in TRIGGERS:
        out.warnings.append(f"{label}: unknown trigger `{trigger}`; imported as a rule loaded on request")
    if trigger == "always_on":
        out.rules.append(Rule(slug, body, provenance))
        return
    scoped = globs(meta.get("globs", "")) if trigger == "glob" else []
    if trigger == "glob" and not scoped:
        out.warnings.append(f"{label}: `trigger: glob` with no globs")
    description = " ".join(meta.get("description", "").split()) if trigger != "manual" else ""
    out.add_skill(slug, description, scoped, body, provenance, label,
                  f"Windsurf's manual rule `{path.stem}`; use when asked to apply it.",
                  "trigger: always_on, glob or model_decision")


def read(path: Path) -> Imported:
    out = Imported()
    plain = path.is_file() and (path.name in NAMES or not _in_rules(path) and not path.read_text(
        encoding="utf-8-sig").startswith("---"))
    if plain:  # plain markdown, always applied
        out.read.add(path.resolve())
        out.rules += to_rules(split(path.read_text(encoding="utf-8-sig")), tilde(path), "windsurf")
        if not out.rules:
            out.warnings.append(f"{tilde(path)}: no text to import")
        return out
    root = path if path.is_dir() else path.parent
    for f in out.files(path, ".md"):
        _rule_file(f, out.unique(_slug(f, root)), tilde(f), out)
    return out
