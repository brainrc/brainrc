"""Cursor rules (#164): `.cursor/rules/**/*.mdc`, and the older `.cursorrules`.

An `alwaysApply: true` rule becomes a rule. A rule scoped by `globs` becomes a skill, with a row in
Gatework's Domains table (`[[extensions.gatework.domains]]`) for those globs, so spec-agent loads
it for those files. A rule with only a `description` (Cursor applies it when the model asks)
becomes a skill with that description; one with neither (applied only when named) becomes a skill
too, and a warning says so. Files are read in path order, which is Cursor's order.
"""
from __future__ import annotations

from pathlib import Path

from ..config import tilde
from ..scaffold import Rule, slugify
from .markdown import globs, split, to_rules, unquote, whole_body
from .model import Imported

NAMES = (".cursorrules",)
LOOK_FOR = (".cursor/rules", ".cursorrules")


def detect(path: Path) -> bool:
    if path.is_file():
        return path.suffix == ".mdc" or path.name == ".cursorrules"
    return path.is_dir() and path.name == "rules" and path.parent.name == ".cursor"


def _rule_file(path: Path, slug: str, label: str, out: Imported) -> None:
    whole = whole_body(path.read_text(encoding="utf-8"))
    if not whole:
        out.warnings.append(f"{label}: no text to import")
        return
    meta, body, first, last = whole  # the file stays one rule or skill: Cursor loads it whole
    provenance = f"imported by brainrc from {label}, lines {first}-{last}"
    scoped = globs(meta.get("globs", ""))
    description = unquote(meta.get("description", ""))
    if meta.get("alwaysApply", "").lower() == "true":
        out.rules.append(Rule(slug, body, provenance))
        return
    out.add_skill(slug, description, scoped, body, provenance, label,
                  f"Cursor's manual rule `{path.stem}`; use when asked to apply it.")


def _slug(path: Path, root: Path) -> str:
    """`frontend/10-react.mdc` -> `frontend-react`: the path, without the ordering number."""
    parts = [*path.relative_to(root).parent.parts, path.stem.lstrip("0123456789-_") or path.stem]
    return slugify("-".join(parts), "rule")


def read(path: Path) -> Imported:
    out = Imported()
    files = [path] if path.is_file() else sorted(path.rglob("*.mdc"), key=lambda p: p.relative_to(path).as_posix())
    for f in files:
        out.read.add(f.resolve())
        label = tilde(f)
        if f.name == ".cursorrules":  # plain markdown, always applied
            out.rules += to_rules(split(f.read_text(encoding="utf-8")), label, "cursorrules")
        else:
            _rule_file(f, _slug(f, path if path.is_dir() else f.parent), label, out)
    if not files:
        out.warnings.append(f"{tilde(path)}: no .mdc files")
    return out
