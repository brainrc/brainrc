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
from .markdown import split, to_rules
from .model import Imported

NAMES = (".cursorrules",)
LOOK_FOR = (".cursor/rules", ".cursorrules")


def detect(path: Path) -> bool:
    if path.is_file():
        return path.suffix == ".mdc" or path.name == ".cursorrules"
    return path.is_dir() and path.name == "rules" and path.parent.name == ".cursor"


def _frontmatter(text: str) -> tuple[dict[str, str], int]:
    """Cursor's frontmatter as written (`globs: *.ts` is not valid YAML, so no YAML parser), and the
    index of the first body line."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return meta, i + 1
        key, sep, value = line.partition(":")
        if sep and key.strip():
            meta[key.strip()] = value.strip()
    return {}, 0  # never closed: all of it is body


def _unquote(value: str) -> str:
    value = value.strip()
    return value[1:-1] if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'" else value


def globs(value: str) -> list[str]:
    """`*.py, scripts/**/*.py` or `["src/**/*.tsx", ...]` -> the globs."""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [g for g in (_unquote(part) for part in value.split(",")) if g]


def _rule_file(path: Path, slug: str, label: str, out: Imported) -> None:
    text = path.read_text(encoding="utf-8")
    meta, start = _frontmatter(text)
    lines = text.splitlines()
    sections = split("\n".join(lines[start:]), start + 1)
    if not sections:
        out.warnings.append(f"{label}: no text to import")
        return
    first, last = sections[0].first, sections[-1].last
    body = "\n".join(lines[first - 1:last])  # the file stays whole: Cursor loads it whole
    provenance = f"imported by brainrc from {label}, lines {first}-{last}"
    scoped = globs(meta.get("globs", ""))
    description = _unquote(meta.get("description", ""))
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
