"""Write a pack's layout: pack.toml, rules/NN-*.md, skills/<prefix>*/SKILL.md.

One small writer for everything that creates a pack: the importers (`brainrc import`, #163) and
`brainrc init`'s import offer use it today, and `brainrc new pack` (#150) is meant to. `render_pack`
returns the files as text, so a caller can show what it would write (file count, tokens) before
`write_pack` touches the disk.
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigError, tilde
from .naming import NAME, PREFIX_MAX, PREFIX_MIN


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

    def __post_init__(self) -> None:
        self.prefix = self.prefix or f"{self.name}-"


SLUG_MAX = 40


def slugify(text: str, fallback: str = "rules") -> str:
    """Lowercase ASCII letters, digits and hyphens from a heading or file name, at most SLUG_MAX."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:SLUG_MAX].strip("-")
    return slug or fallback


def check_name(name: str, prefix: str) -> None:
    """The naming rules a pack's own name and prefix must meet before anything is written."""
    stem = prefix[:-1] if prefix.endswith("-") else prefix
    if not NAME.fullmatch(name):
        raise ConfigError(f"pack name `{name}`: use ASCII lowercase letters, digits and hyphens")
    if not prefix.endswith("-") or not NAME.fullmatch(stem) or not PREFIX_MIN <= len(stem) <= PREFIX_MAX:
        raise ConfigError(f"prefix `{prefix}`: {PREFIX_MIN} to {PREFIX_MAX} lowercase letters, digits "
                          "and hyphens, then '-'")


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
    check_name(spec.name, spec.prefix)
    files: dict[str, str] = {}
    lines = [f"name = {_toml_string(spec.name)}", f"prefix = {_toml_string(spec.prefix)}"]
    if spec.description:
        lines.append(f"description = {_toml_string(spec.description)}")
    lines.append(f"requires_core = {_toml_string(spec.requires_core or _core_pin())}")
    for row in spec.domains:
        lines += ["", "[[extensions.gatework.domains]]",
                  f"files = {_toml_string(row['files'])}",
                  "skills = [" + ", ".join(_toml_string(s) for s in row["skills"]) + "]"]
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
    return files


def write_pack(dest: Path, files: dict[str, str], force: bool = False) -> list[Path]:
    """Write files under dest, all or nothing: into a temporary directory beside dest, then moved
    into place. dest must not exist, or be empty, unless force, which replaces it."""
    if dest.exists() and not dest.is_dir():
        raise ConfigError(f"{tilde(dest)} is a file, not a directory")
    if dest.is_dir() and any(dest.iterdir()) and not force:
        raise ConfigError(f"{tilde(dest)} already has files; pick another directory, or pass --force "
                          "to replace it")
    for rel in files:
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ConfigError(f"refusing to write {rel} outside {tilde(dest)}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{dest.name}-", dir=dest.parent))
    try:
        for rel, text in files.items():
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(tmp, dest)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return [dest / rel for rel in files]
