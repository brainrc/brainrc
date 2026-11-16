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
from ..scaffold import Rule, Skill, slugify
from ..sources import parse_frontmatter
from .markdown import split, to_rules
from .model import Imported

NAMES = (".cursorrules",)
LOOK_FOR = (".cursor/rules", ".cursorrules")


def detect(path: Path) -> bool:
    if path.is_file():
        return path.suffix == ".mdc" or path.name == ".cursorrules"
    return path.is_dir() and path.name == "rules" and path.parent.name == ".cursor"


def _unquote(value: str) -> str:
    value = value.strip()
    return value[1:-1] if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'" else value


def globs(value: str) -> list[str]:
    """`*.py, scripts/**/*.py`, `"*.py, *.pyi"`, `["src/**/*.tsx", ...]` or `src/*.{ts,tsx}` -> the
    globs: split at commas outside `{}` and `[]`, each unquoted."""
    value = _unquote(value)
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    parts, depth, cur = [], 0, ""
    for ch in value:
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        depth += {"{": 1, "[": 1, "}": -1, "]": -1}.get(ch, 0)
        cur += ch
    parts.append(cur)
    return [g for g in (_unquote(part) for part in parts) if g]


def _rule_file(path: Path, slug: str, label: str, out: Imported) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    meta, start = parse_frontmatter(lines)
    sections = split("\n".join(lines[start:]), start + 1)
    if not sections:
        out.warnings.append(f"{label}: no text to import")
        return
    first, last = sections[0].first, sections[-1].last
    body = "\n".join(lines[first - 1:last])  # the file stays whole: Cursor loads it whole
    provenance = f"imported by brainrc from {label}, lines {first}-{last}"
    scoped = globs(meta.get("globs", ""))
    description = " ".join(meta.get("description", "").split())
    if meta.get("alwaysApply", "").lower() == "true":
        out.rules.append(Rule(slug, body, provenance))
        return
    if scoped:
        where = ", ".join(f"`{g}`" for g in scoped)
        description = (f"{description.rstrip('.')}. " if description else "") + f"Use when working on {where}."
        out.domains.append({"files": where, "skills": [slug]})
    elif not description:
        description = f"Cursor's manual rule `{path.stem}`; use when asked to apply it."
        out.warnings.append(f"{label}: has no description, globs or alwaysApply, so it becomes a skill "
                            "the model loads only when asked")
    out.skills.append(Skill(slug, description, body, provenance))


def _unique(slug: str, out: Imported) -> str:
    """slug, or slug-2, -3... when this source already has a skill or rule of that name."""
    taken = {s.slug for s in out.skills} | {r.slug for r in out.rules}
    name, n = slug, 2
    while name in taken:
        name, n = f"{slug}-{n}", n + 1
    return name


def _slug(path: Path, root: Path) -> str:
    """`10-frontend/20-react.mdc` -> `frontend-react`: the path, without the ordering numbers."""
    parts = [p.lstrip("0123456789-_") or p for p in (*path.relative_to(root).parent.parts, path.stem)]
    return slugify("-".join(parts), "rule")


def read(path: Path) -> Imported:
    out = Imported()
    files = [path] if path.is_file() else sorted(path.rglob("*.mdc"), key=lambda p: p.relative_to(path).as_posix())
    for f in files:
        out.read.add(f.resolve())
        label = tilde(f)
        if f.name == ".cursorrules":  # plain markdown, always applied
            rules = to_rules(split(f.read_text(encoding="utf-8-sig")), label, "cursorrules")
            out.rules += rules
            if not rules:
                out.warnings.append(f"{label}: no text to import")
        else:
            _rule_file(f, _unique(_slug(f, path if path.is_dir() else f.parent), out), label, out)
    if not files:
        out.warnings.append(f"{tilde(path)}: no .mdc files")
    return out
