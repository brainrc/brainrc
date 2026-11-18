"""Write a pack's layout: pack.toml, rules/NN-*.md, skills/<prefix>*/SKILL.md.

One small writer for everything that creates a pack: the importers (`brainrc import`, #163),
`brainrc init`'s import offer and `brainrc new pack` (#150, brainrc/newpack.py). `render_pack`
returns the files as text, so a caller can show what it would write (file count, tokens) before
`write_pack` touches the disk.
"""
from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath

from . import config
from .config import ConfigError, tilde
from .naming import name_errors


@dataclass
class Rule:
    slug: str        # the file name after NN- (`git`, `testing`)
    text: str        # the rule's markdown, as the source had it
    provenance: str = ""  # where it came from, kept as a comment on the first line


@dataclass
class Skill:
    slug: str        # the skill's name after the pack prefix
    description: str
    text: str        # SKILL.md's body
    provenance: str = ""


@dataclass
class PackSpec:
    name: str
    prefix: str = ""          # default: "<name>-"
    description: str = ""
    requires_core: str = ""   # default: this core's minor series
    rules: list[Rule] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    domains: list[dict] = field(default_factory=list)  # [[extensions.gatework.domains]] rows
    id: str = ""              # <owner>/<pack>, when it is published under one
    max_always_tokens: int = 0
    test: str = ""            # the pack's own tests, which validate --pack runs
    ticket: dict = field(default_factory=dict)  # [extensions.gatework.ticket]: strings and lists of strings
    files: dict[str, str] = field(default_factory=dict)  # any other file, path -> text, written last
    notes: dict[str, str] = field(default_factory=dict)  # pack.toml key -> a comment at the end of its line

    def __post_init__(self) -> None:
        self.prefix = self.prefix or f"{self.name}-"


SLUG_MAX = 40
# Taplo's directive for pack.toml's JSON Schema: completion and checks in editors (docs/packs.md).
PACK_SCHEMA = "#:schema https://raw.githubusercontent.com/brainrc/brainrc/main/docs/schemas/pack.toml.schema.json"


def slugify(text: str, fallback: str = "rules") -> str:
    """Lowercase ASCII letters, digits and hyphens from a heading or file name, at most SLUG_MAX."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:SLUG_MAX].strip("-")
    return slug or fallback


def check_name(name: str, prefix: str, pack_id: str = "") -> None:
    """The naming rules (docs/packs.md#naming) a pack's own name, prefix and ID must meet before
    anything is written."""
    errors = name_errors(name, prefix, pack_id or None, "pack")
    if errors:
        raise ConfigError("; ".join(e.removeprefix("pack: ") for e in errors))


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _core_pin() -> str:
    from .sources import core_version  # late: sources reads config at call time
    major, minor = core_version()[:2]
    return f">={major}.{minor}, <{major}.{minor + 1}" if major == 0 else f">={major}.{minor}, <{major + 1}"


def _comment(provenance: str) -> str:
    return f"<!-- {provenance.replace('--', '- -')} -->\n\n" if provenance else ""


def rule_files(rules: list[Rule]) -> list[tuple[str, str]]:
    """(rules/NN-slug.md, text) in order. NN steps by 10 for up to nine rules (room to insert one
    later), else by 1, with as many digits as the count needs so filename order is rule order."""
    step = 10 if len(rules) <= 9 else 1
    width = max(2, len(str(len(rules) * step)))
    return [(f"rules/{(i + 1) * step:0{width}d}-{r.slug}.md", f"{_comment(r.provenance)}{r.text.strip()}\n")
            for i, r in enumerate(rules)]


def _frontmatter_value(value: str) -> str:
    return _toml_string(" ".join(value.split()))  # a JSON-style double-quoted scalar is valid YAML too


def render_pack(spec: PackSpec) -> dict[str, str]:
    """The pack's files, path -> text, in the order they are written."""
    check_name(spec.name, spec.prefix, spec.id)
    files: dict[str, str] = {}

    def key(name: str, value: str) -> str:
        note = spec.notes.get(name)
        return f"{name} = {value}" + (f"  # {note}" if note else "")

    lines = [PACK_SCHEMA, key("name", _toml_string(spec.name)), key("prefix", _toml_string(spec.prefix))]
    if spec.id:
        lines.append(key("id", _toml_string(spec.id)))
    if spec.description:
        lines.append(key("description", _toml_string(spec.description)))
    lines.append(key("requires_core", _toml_string(spec.requires_core or _core_pin())))
    if spec.max_always_tokens:
        lines.append(key("max_always_tokens", str(spec.max_always_tokens)))
    if spec.test:
        lines.append(key("test", _toml_string(spec.test)))
    for row in spec.domains:
        lines += ["", "[[extensions.gatework.domains]]",
                  f"files = {_toml_string(row['files'])}",
                  "skills = [" + ", ".join(_toml_string(s) for s in row["skills"]) + "]"]
    if spec.ticket:
        lines += ["", "[extensions.gatework.ticket]"]
        lines += [f"{k} = " + ("[" + ", ".join(map(_toml_string, v)) + "]" if isinstance(v, list) else _toml_string(v))
                  for k, v in spec.ticket.items()]
    files["pack.toml"] = "\n".join(lines) + "\n"
    files.update(rule_files(spec.rules))
    seen: set[str] = set()
    for s in spec.skills:
        name = f"{spec.prefix}{s.slug}"
        n = 2
        while name in seen:  # two sources with the same name: keep both
            name, n = f"{spec.prefix}{s.slug}-{n}", n + 1
        seen.add(name)
        files[f"skills/{name}/SKILL.md"] = (
            f"---\nname: {name}\ndescription: {_frontmatter_value(s.description)}\n---\n\n"
            f"{_comment(s.provenance)}{s.text.strip()}\n")
    for rel, text in spec.files.items():
        if rel in files:
            raise ConfigError(f"{rel} is written twice")
        files[rel] = text
    return files


def check_dest(dest: Path, files: dict[str, str], force: bool = False, sources: list[Path] = ()) -> None:
    """Raise ConfigError if write_pack would refuse dest: so a caller can check before it asks."""
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
        raise ConfigError(f"{tilde(dest)} is a link or a file, not a folder")
    full = dest.is_dir() and any(dest.iterdir())
    if full and not force:
        raise ConfigError(f"{tilde(dest)} already has files; pick another folder, or pass --force "
                          "to replace the pack in it")
    if full and not (dest / "pack.toml").is_file():
        raise ConfigError(f"{tilde(dest)} has files but no pack.toml; --force replaces only an earlier pack")
    held = [s for s in sources if s.resolve().is_relative_to(dest.resolve())]
    if full and held:
        raise ConfigError(f"{tilde(dest)} holds {tilde(held[0])}, which is being imported; pick another folder")
    for rel in files:
        posix, win = PurePosixPath(rel), PureWindowsPath(rel)
        if posix.is_absolute() or win.is_absolute() or win.drive or win.root or ".." in win.parts:
            raise ConfigError(f"refusing to write {rel} outside {tilde(dest)}")


def write_pack(dest: Path, files: dict[str, str], force: bool = False, sources: list[Path] = ()) -> list[Path]:
    """Write files under dest: into a temporary folder beside it, then moved into place. dest must
    not exist, or be empty. With force it may also be an earlier pack (it has a pack.toml), which
    is replaced, but never a folder that holds one of the sources or is a link."""
    check_dest(dest, files, force, sources)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{dest.name}-", dir=dest.parent))
    old = None
    try:
        for rel, text in files.items():
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        if dest.exists():  # moved aside first, so a failure leaves the earlier pack whole
            old = Path(tempfile.mkdtemp(prefix=f".{dest.name}-old-", dir=dest.parent))
            os.replace(dest, old / dest.name)
        os.replace(tmp, dest)
    except BaseException:
        if old and not dest.exists():
            os.replace(old / dest.name, dest)
        config.rmtree(tmp, ignore_errors=True)
        raise
    finally:
        if old:
            config.rmtree(old, ignore_errors=True)
    return [dest / rel for rel in files]
