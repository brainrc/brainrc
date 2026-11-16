"""Connector config: a skill declares the keys a pack's table may set for it, and validate checks
every table that names the skill as its `connector` (#136).

A connector declares its config in SKILL.md frontmatter, under the Agent Skills `metadata` map (so
harnesses that follow the spec load it unchanged), as one string of `key: type` entries:

    metadata:
      brainrc-config: "refs: list required; host: string required; blocked_status: string"

Types: string, integer, boolean, list (of strings). `required` makes a key mandatory. Every table
may also set `connector` and `instructions`, a defined field for the free-form guidance a pack
gives the connector, which the pack's tripwires check like its other text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import did_you_mean, key_line
from .sources import Source, _quoted, parse_frontmatter, skills

CONFIG_KEY = "brainrc-config"
TYPES = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
}
WANT = {"string": "a string", "integer": "an integer", "boolean": "true or false", "list": "a list of strings"}
RESERVED = {"connector": "string", "instructions": "string"}  # every connector table may set these
RENAMED = {"notes": "instructions"}  # free-form keys a defined field replaced
ENTRY = re.compile(r"^([a-z][a-z0-9_]*)\s*:\s*([a-z]+)(\s+required)?$")


@dataclass(frozen=True)
class Field:
    kind: str
    required: bool = False


def metadata(path: Path) -> dict[str, str]:
    """The one-level `metadata:` map of a file's frontmatter, every value a string. A value may be
    plain, quoted, or a `>`/`|` block scalar, and may wrap onto more-indented lines; keys nested
    deeper than the map's own are part of a value, not keys of it."""
    lines = path.read_text().splitlines()
    end = parse_frontmatter(lines)[1]
    found: dict[str, list[str]] = {}
    inside, indent, key = False, None, None
    for line in lines[1:max(end - 1, 1)]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            inside, indent, key = line.split("#", 1)[0].strip() == "metadata:", None, None
            continue
        if not inside:
            continue
        depth = len(line) - len(line.lstrip())
        indent = depth if indent is None else indent
        if depth == indent and (m := re.match(r"^\s+([^\s:#][^:]*?):(?:\s+(.*))?$", line)):
            key = m[1]
            found[key] = [(m[2] or "").strip()]
        elif depth > indent and key:
            found[key].append(line.strip())
    return {k: _scalar(v) for k, v in found.items()}


def _scalar(parts: list[str]) -> str:
    """One YAML scalar from its first line and its continuation lines."""
    head, rest = parts[0], parts[1:]
    if head[:1] in ("|", ">"):
        return ("\n" if head[0] == "|" else " ").join(rest)
    if head[:1] in "'\"" and head:
        return _quoted(" ".join([head, *rest]))
    return " ".join([head.split(" #", 1)[0].strip(), *rest]).strip()


def parse(text: str) -> tuple[dict[str, Field], list[str]]:
    """(fields, problems) from a `brainrc-config` value."""
    fields: dict[str, Field] = {}
    problems = []
    for entry in (e.strip() for e in text.split(";")):
        if not entry:
            continue
        m = ENTRY.match(entry)
        if not m or m[2] not in TYPES:
            problems.append(f"`{entry}` must be `key: type` with a type of {', '.join(TYPES)}, "
                            "then `required` if the key must be set")
        elif m[1] in fields or m[1] in RESERVED:
            problems.append(f"`{m[1]}` is declared twice" if m[1] in fields
                            else f"`{m[1]}` is set for every connector; don't declare it")
        else:
            fields[m[1]] = Field(m[2], bool(m[3]))
    return fields, problems


def declared(skill: Path) -> dict[str, Field] | None:
    """A skill's declared config, or None when it declares none or a broken one (it is then not
    checked: the skill's own error says what to fix, and packs aren't told to drop good keys)."""
    text = metadata(skill / "SKILL.md").get(CONFIG_KEY)
    if text is None:
        return None
    fields, problems = parse(text)
    return None if problems else fields


def declaration_errors(src: Source) -> list[str]:
    """Problems with the `brainrc-config` of each of src's skills."""
    errors = []
    for s in skills(src):
        text = metadata(s / "SKILL.md").get(CONFIG_KEY)
        if text is not None:
            errors += [f"{src.rel(s)}/SKILL.md: metadata.{CONFIG_KEY}: {p}" for p in parse(text)[1]]
    return errors


def tables(meta: dict) -> list[tuple[str, dict]]:
    """(TOML name, table) for every table under [extensions] that names a `connector`: a namespace's
    own tables ([extensions.gatework.ticket]) and the legacy top-level ones ([extensions.ticket])."""
    ext = meta.get("extensions")
    found = []
    for key, value in (ext.items() if isinstance(ext, dict) else []):
        if not isinstance(value, dict):
            continue
        if "connector" in value:
            found.append((f"extensions.{key}", value))
        found += [(f"extensions.{key}.{k}", v) for k, v in value.items()
                  if isinstance(v, dict) and "connector" in v]
    return found


def check(src: Source, connectors: dict[str, Path]) -> tuple[list[str], list[str]]:
    """(errors, warnings) for src's connector tables against each named connector's declaration:
    a key of the wrong type or a missing required key fails; a key the connector doesn't declare
    warns. connectors: every skill name, across the sources, to its folder."""
    path = src.root / "pack.toml"
    if not path.is_file():
        return [], []
    text = path.read_text()
    errors, warnings = [], []
    for name, table in tables(src.meta):
        connector = table.get("connector")
        skill = connectors.get(connector) if isinstance(connector, str) else None
        fields = declared(skill) if skill else None
        where = f"{src.rel(path)}: [{name}]"
        for key in ("connector", "instructions"):
            if key in table and not isinstance(table[key], str):
                errors.append(f"{where} `{key}` must be a string")
        if fields is None:
            continue
        whose = f"({connector}'s config)"
        for key, field in fields.items():
            if key not in table:
                if field.required:
                    errors.append(f"{where} needs `{key}` {whose}")
            elif not TYPES[field.kind](table[key]):
                errors.append(f"{where} `{key}` must be {WANT[field.kind]} {whose}")
        for key in table:
            if key in fields or key in RESERVED:
                continue
            at = f"{src.rel(path)}:{key_line(text, (*name.split('.'), key))}: [{name}]"
            hint = f"; it is now `{RENAMED[key]}`" if key in RENAMED else did_you_mean(key, fields)
            warnings.append(f"{at} unknown key `{key}` for {connector}{hint}; it ignores it")
    return errors, warnings


def instruction_texts(src: Source) -> list[tuple[str, str]]:
    """(TOML name, text) of every connector table's `instructions`, for the pack's tripwires."""
    return [(name, t["instructions"]) for name, t in tables(src.meta) if isinstance(t.get("instructions"), str)]
