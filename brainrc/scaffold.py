"""Write a pack's layout: pack.toml, rules/NN-*.md, skills/<prefix>*/SKILL.md, agents, commands,
MCP servers and any other file.

One small writer for everything that creates a pack or an item in one: the importers
(`brainrc import`, #163), `brainrc init`'s import offer, `brainrc new pack` (#150,
brainrc/newpack.py) and `brainrc new skill|agent|rule|command` (E8, brainrc/newitem.py).
`render_pack` returns the files, so a caller can show what it would write (file count, tokens)
before `write_pack` touches the disk; `add_files` writes new items into a pack that exists.
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
    extra: list[str] = field(default_factory=list)  # other frontmatter lines, as written
    files: dict[str, str | Copied] = field(default_factory=dict)  # its other files, by path in its folder


@dataclass(frozen=True)
class Copied:
    """A file copied as it was: its bytes, and whether it was executable where it came from."""
    data: bytes
    executable: bool = False


@dataclass
class Agent:
    slug: str        # the agent's name after the pack prefix
    description: str
    text: str        # the system prompt
    provenance: str = ""
    tools: str = ""  # `Read, Grep, Glob`; empty inherits every tool
    model: str = ""
    extra: list[str] = field(default_factory=list)


@dataclass
class Command:
    slug: str        # the command's name after the pack prefix
    description: str
    text: str        # the prompt; $ARGUMENTS is what follows the command
    provenance: str = ""
    extra: list[str] = field(default_factory=list)


@dataclass
class PackSpec:
    name: str
    prefix: str = ""          # default: "<name>-"
    description: str = ""
    requires_core: str = ""   # default: this core's minor series
    rules: list[Rule] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)
    servers: dict[str, dict] = field(default_factory=dict)  # mcp/servers.toml, by name after the prefix
    domains: list[dict] = field(default_factory=list)  # [[extensions.gatework.domains]] rows
    id: str = ""              # <owner>/<pack>, when it is published under one
    max_always_tokens: int = 0
    test: str = ""            # the pack's own tests, which validate --pack runs
    ticket: dict = field(default_factory=dict)  # [extensions.gatework.ticket]: strings and lists of strings
    files: dict[str, str | Copied] = field(default_factory=dict)  # any other file, path -> content, written last
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
    from .sources import default_packs  # late: sources reads config at call time
    taken = ["core", *default_packs()]
    if name in taken:
        errors.append(f"pack: `name` `{name}` is taken by brainrc ({', '.join(taken)})")
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
    return [(f"rules/{(i + 1) * step:0{width}d}-{r.slug}.md", render_rule(r)) for i, r in enumerate(rules)]


def _frontmatter_value(value: str) -> str:
    return _toml_string(" ".join(value.split()))  # a JSON-style double-quoted scalar is valid YAML too


def _frontmatter(fields: list[tuple[str, str]], extra: list[str] = ()) -> str:
    lines = [f"{k}: {v}" for k, v in fields if v] + [line.rstrip() for line in extra]
    return "---\n" + "\n".join(lines) + "\n---\n\n"


def skill_text(name: str, s: Skill) -> str:
    """SKILL.md for the skill `name` (prefix included)."""
    fields = [("name", name), ("description", _frontmatter_value(s.description))]
    return f"{_frontmatter(fields, s.extra)}{_comment(s.provenance)}{s.text.strip()}\n"


def agent_text(name: str, a: Agent) -> str:
    """agents/<name>.md in Claude Code's subagent format (docs/formats.md#agents-agentsnamemd)."""
    fields = [("name", name), ("description", _frontmatter_value(a.description)), ("tools", a.tools),
              ("model", a.model)]
    return f"{_frontmatter(fields, a.extra)}{_comment(a.provenance)}{a.text.strip()}\n"


def command_text(c: Command) -> str:
    """commands/<name>.md: a description and a prompt (docs/formats.md#commands-commandsnamemd)."""
    return f"{_frontmatter([('description', _frontmatter_value(c.description))], c.extra)}" \
           f"{_comment(c.provenance)}{c.text.strip()}\n"


def render_rule(r: Rule, frontmatter: bool = False) -> str:
    """A rule file's text. frontmatter: core's `trigger: always_on` and `alwaysApply: true`, which
    Antigravity and Cursor need and brainrc strips when it renders the instructions file."""
    head = "---\ntrigger: always_on\nalwaysApply: true\n---\n\n" if frontmatter else ""
    return f"{head}{_comment(r.provenance)}{r.text.strip()}\n"


def servers_text(servers: dict[str, dict]) -> str:
    """mcp/servers.toml for these servers (docs/formats.md#mcp-servers-mcpserverstoml)."""
    def value(v) -> str:
        return "[" + ", ".join(map(_toml_string, v)) + "]" if isinstance(v, list) else _toml_string(v)
    tables = []
    for name, table in servers.items():
        key = name if re.fullmatch(r"[A-Za-z0-9_-]+", name) else _toml_string(name)
        tables.append("\n".join([f"[servers.{key}]", *(f"{k} = {value(v)}" for k, v in table.items())]))
    return "\n\n".join(tables) + "\n"


def _unique(prefix: str, slug: str, seen: set[str]) -> str:
    """prefix + slug, numbered -2, -3... when an item of that kind already has the name: two
    sources with the same name keep both."""
    name, n = f"{prefix}{slug}", 2
    while name in seen:
        name, n = f"{prefix}{slug}-{n}", n + 1
    seen.add(name)
    return name


def domains_row(files: str, skills: list[str]) -> str:
    """One [[extensions.gatework.domains]] row: the files (`glob`, ...) and the skills they load."""
    return (f"[[extensions.gatework.domains]]\nfiles = {_toml_string(files)}\n"
            f"skills = [{', '.join(map(_toml_string, skills))}]\n")


def render_pack(spec: PackSpec) -> dict[str, str | Copied]:
    """The pack's files, path -> text, in the order they are written."""
    check_name(spec.name, spec.prefix, spec.id)
    files: dict[str, str | Copied] = {}

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
        lines += ["", *domains_row(row["files"], row["skills"]).splitlines()]
    if spec.ticket:
        lines += ["", "[extensions.gatework.ticket]"]
        lines += [f"{k} = " + ("[" + ", ".join(map(_toml_string, v)) + "]" if isinstance(v, list) else _toml_string(v))
                  for k, v in spec.ticket.items()]
    files["pack.toml"] = "\n".join(lines) + "\n"
    files.update(rule_files(spec.rules))
    seen: set[str] = set()
    for s in spec.skills:
        name = _unique(spec.prefix, s.slug, seen)
        files[f"skills/{name}/SKILL.md"] = skill_text(name, s)
        for rel, data in s.files.items():
            files[f"skills/{name}/{rel}"] = data
    seen = set()
    for a in spec.agents:
        name = _unique(spec.prefix, a.slug, seen)
        files[f"agents/{name}.md"] = agent_text(name, a)
    seen = set()
    for c in spec.commands:
        files[f"commands/{_unique(spec.prefix, c.slug, seen)}.md"] = command_text(c)
    if spec.servers:
        seen = set()
        files["mcp/servers.toml"] = servers_text({_unique(spec.prefix, n, seen): t for n, t in spec.servers.items()})
    for rel, text in spec.files.items():
        if rel in files:
            raise ConfigError(f"{rel} is written twice")
        files[rel] = text
    return files


def check_dest(dest: Path, files: dict[str, str | Copied], force: bool = False, sources: list[Path] = ()) -> None:
    """Raise ConfigError if write_pack would refuse dest: so a caller can check before it asks."""
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
        raise ConfigError(f"{tilde(dest)} is a link or a file, not a folder")
    full = dest.is_dir() and any(p.name != ".git" for p in dest.iterdir())  # a fresh clone is empty
    if full and not force:
        raise ConfigError(f"{tilde(dest)} already has files; pick another folder, or pass --force "
                          "to replace the pack in it")
    if full and not (dest / "pack.toml").is_file():
        raise ConfigError(f"{tilde(dest)} has files but no pack.toml; --force replaces only an earlier pack")
    held = [s for s in sources if s.resolve().is_relative_to(dest.resolve())]
    if full and held:
        raise ConfigError(f"{tilde(dest)} holds {tilde(held[0])}, which is being imported; pick another folder")
    _check_paths(dest, files)


def _check_paths(dest: Path, files: dict) -> None:
    for rel in files:
        posix, win = PurePosixPath(rel), PureWindowsPath(rel)
        if posix.is_absolute() or win.is_absolute() or win.drive or win.root or ".." in win.parts:
            raise ConfigError(f"refusing to write {rel} outside {tilde(dest)}")


def _write(path: Path, data: str | Copied) -> None:
    """One file: text as UTF-8 with \n line ends, a copied file byte for byte. A copied file keeps
    its executable bit; text that starts with `#!` is a script, so it is made executable."""
    if isinstance(data, Copied):
        path.write_bytes(data.data)
    else:
        path.write_text(data, encoding="utf-8", newline="\n")
    if data.executable if isinstance(data, Copied) else data.startswith("#!"):
        path.chmod(path.stat().st_mode | 0o111)


def write_pack(dest: Path, files: dict[str, str | Copied], force: bool = False, sources: list[Path] = ()) -> list[Path]:
    """Write files under dest: into a temporary folder beside it, then moved into place. dest must
    not exist, or be empty but for `.git`. With force it may also be an earlier pack (it has a
    pack.toml), which is replaced, but never a folder that holds one of the sources or is a link.
    dest's `.git` is kept: it moves into the new folder, so the history stays."""
    check_dest(dest, files, force, sources)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{dest.name}-", dir=dest.parent))
    git = dest / ".git"
    old = None
    try:
        for rel, data in files.items():
            path = tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            _write(path, data)
        if git.exists() and not git.is_symlink():
            os.replace(git, tmp / ".git")
        if dest.exists():  # moved aside first, so a failure leaves the earlier pack whole
            old = Path(tempfile.mkdtemp(prefix=f".{dest.name}-old-", dir=dest.parent))
            os.replace(dest, old / dest.name)
        os.replace(tmp, dest)
    except BaseException:
        if old and not dest.exists():
            os.replace(old / dest.name, dest)
        if (tmp / ".git").exists() and dest.is_dir() and not git.exists():
            os.replace(tmp / ".git", git)
        config.rmtree(tmp, ignore_errors=True)
        raise
    finally:
        if old:
            config.rmtree(old, ignore_errors=True)
    return [dest / rel for rel in files]


def add_files(root: Path, files: dict[str, str], force: bool = False) -> list[Path]:
    """Write new items into the pack at root (`brainrc new skill` and the like): each file through
    a temporary file beside it. Refuses, before writing any, a file that exists unless force (then
    it is replaced), a path outside root, and a path through a link."""
    _check_paths(root, files)
    for rel in files:
        path = root / rel
        for parent in [path, *path.parents]:
            if parent == root:
                break
            if parent.is_symlink():
                raise ConfigError(f"{tilde(parent)} is a link; refusing to write {rel} through it")
        if path.exists() and not force:
            raise ConfigError(f"{tilde(path)} already exists; pick another name, or pass --force to replace it")
        if path.exists() and not path.is_file():
            raise ConfigError(f"{tilde(path)} is not a file")
    written = []
    for rel, text in files.items():
        path = root / rel
        config.write_text_atomic(path, text)
        written.append(path)
    return written
