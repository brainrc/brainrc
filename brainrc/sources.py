"""Sources (core and packs), their items, and the rule and extension renders."""
from __future__ import annotations

import fnmatch
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .config import (
    CHANGELOG_UNRELEASED,
    CHANGELOG_VERSION,
    COMPARE,
    CONSTRAINT_CLAUSE,
    CONSTRAINT_SYNTAX,
    CORE_VERSION,
    ConfigError,
    KINDS,
    _layered,
    _read_toml,
    expand,
    line_of,
    tilde,
    toml_error,
)


@dataclass
class Source:
    name: str             # "core" or the pack name
    root: Path
    prefix: str = ""      # required name prefix for a pack's skills, agents, commands
    meta: dict = field(default_factory=dict)  # pack.toml
    key: str = ""         # the pack's table in packs.toml ("" for core and validate --pack)

    @property
    def is_core(self) -> bool:
        return self.name == "core"

    @property
    def default(self) -> bool:
        """A default pack: one core's own packs.toml lists (Gatework), wherever this machine gets it.
        `validate --pack` has no table key, so a pack it checks counts by its name."""
        return not self.is_core and (self.key or self.name) in default_packs()

    def rel(self, path: Path) -> str:
        rel = str(path.relative_to(self.root))
        return rel if self.is_core else f"{self.name}:{rel}"


def load_pack(root: Path, name: str | None = None) -> Source:
    pack_toml = root / "pack.toml"
    if not pack_toml.is_file():
        raise ConfigError(f"pack {name or root}: no pack.toml at {tilde(pack_toml)}")
    text = pack_toml.read_text()
    try:
        meta = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise toml_error(pack_toml, text, e) from None
    for key in ("name", "prefix"):
        if key in meta and not isinstance(meta[key], str):
            raise ConfigError(f"{tilde(pack_toml)}:{line_of(text, key)}: `{key}` must be a string")
    pack_name = meta.get("name", name or root.name)
    return Source(pack_name, root, meta.get("prefix", f"{pack_name}-"), meta, name or "")


def core_version() -> tuple[int, ...]:
    """The core version from VERSION: the contract packs pin with `requires_core`."""
    path = config.REPO / "VERSION"
    if not path.is_file():
        raise ConfigError("VERSION: missing (expected MAJOR.MINOR.PATCH)")
    text = path.read_text().strip()
    m = CORE_VERSION.match(text)
    if not m:
        raise ConfigError(f"VERSION: `{text}` is not MAJOR.MINOR.PATCH")
    return tuple(int(n) for n in m.groups())


def check_changelog(core: tuple[int, ...]) -> list[str]:
    """main is what users pull: no Unreleased, newest entry = VERSION (release keeps them in step)."""
    version = ".".join(map(str, core))
    path = config.REPO / "CHANGELOG.md"
    if not path.is_file():
        return [f"CHANGELOG.md: missing (add your entries under `## {version}`)"]
    text = path.read_text()
    errors = []
    if CHANGELOG_UNRELEASED.search(text):
        errors.append(f"CHANGELOG.md: has an `## Unreleased` section. Put its entries under `## {version}`.")
    m = CHANGELOG_VERSION.search(text)
    if not m:
        errors.append(f"CHANGELOG.md: no `## X.Y.Z` heading (expected `## {version}`)")
    elif m.group(1) != version:
        errors.append(f"CHANGELOG.md: newest version {m.group(1)} doesn't match VERSION {version}. "
                      "`brainrc.py release` updates both.")
    return errors


def parse_constraint(text: str) -> list[tuple[str, tuple[int, ...]]]:
    """'>=0.1, <0.2' -> [('>=', (0, 1, 0)), ('<', (0, 2, 0))]. A bare version means >=."""
    clauses = []
    for part in text.split(","):
        m = CONSTRAINT_CLAUSE.match(part.strip())
        if not m:
            raise ValueError(f"expected {CONSTRAINT_SYNTAX}")
        parts = [int(n) for n in m.group(2).split(".")]
        clauses.append((m.group(1) or ">=", tuple(parts + [0] * (3 - len(parts)))))
    return clauses


def satisfies(version: tuple[int, ...], clauses: list[tuple[str, tuple[int, ...]]]) -> bool:
    return all(COMPARE[op](version, bound) for op, bound in clauses)


def pack_compat(src: Source, core: tuple[int, ...]) -> tuple[list[str], list[str]]:
    """(errors, warnings) for one pack's `requires_core` against the core version."""
    where = f"{src.name}:pack.toml"
    text = src.meta.get("requires_core")
    if text is None:
        # Suggest the pin docs/packs.md recommends: breaking changes bump MINOR in 0.x, MAJOR after.
        major, minor = core[0], core[1]
        pin = f">=0.{minor}, <0.{minor + 1}" if major == 0 else f">={major}.{minor}, <{major + 1}"
        return [], [f'{where}: no `requires_core`; add e.g. requires_core = "{pin}" '
                    "so incompatible core changes are caught (docs/packs.md)"]
    try:
        clauses = parse_constraint(str(text))
    except ValueError as e:
        return [f"{where}: invalid requires_core `{text}`: {e}"], []
    if not satisfies(core, clauses):
        return [f"{where}: requires_core `{text}` is not satisfied by core "
                f"{'.'.join(map(str, core))}"], []
    return [], []


def check_packs(srcs: list[Source]) -> tuple[list[str], list[str]]:
    """(errors, warnings) for every pack in srcs. Reads VERSION only when there are packs."""
    packs = [s for s in srcs if not s.is_core]
    if not packs:
        return [], []
    core = core_version()
    errors, warnings = [], []
    for src in packs:
        e, w = pack_compat(src, core)
        errors += e
        warnings += w
    return errors, warnings


_DEFAULT_PACKS: dict[str, list[str]] = {}


def default_packs() -> list[str]:
    """The packs core's own packs.toml lists, in order: on unless packs.local.toml says `enabled = false`.
    Parsed once per text: Source.default asks for every source."""
    path = config.REPO / "packs.toml"
    text = path.read_text() if path.is_file() else ""
    if text not in _DEFAULT_PACKS:
        _DEFAULT_PACKS[text] = [k for k, v in _read_toml(path).items() if isinstance(v, dict)] if text else []
    return _DEFAULT_PACKS[text]


def _pack_root(cfg: dict, key: str) -> Path:
    if ("path" in cfg) == ("git" in cfg):
        raise ConfigError(f"packs.toml [{key}]: set `path` or `git` (one of them)")
    if "git" in cfg:
        return config.settings_home() / "packs" / key  # fetched by brainrc (brainrc/packs.py)
    root = expand(str(cfg["path"]))
    return root if root.is_absolute() else config.local_dir() / root  # beside packs.local.toml


def sources(include_disabled: bool = False) -> list[Source]:
    """Core first, then packs in packs.toml order. Disabled packs are only listed (without
    reading pack.toml) when include_disabled is set, so their old links can be pruned."""
    found = [Source("core", config.REPO)]
    for key, cfg in _layered("packs").items():
        enabled = cfg.get("enabled", True)
        if not enabled and not include_disabled:
            continue
        root = _pack_root(cfg, key)
        if "git" in cfg and not root.exists():
            continue  # not fetched yet: apply fetches it, status and doctor report it
        found.append(load_pack(root, key) if enabled else Source(key, root))
    return found


def default_sources(skip: str = "") -> tuple[list[Source], list[str]]:
    """The enabled default packs this machine has on disk (fetched, or a local `path`): what
    `validate --pack` checks a pack against, since a pack may use their skills and agents.
    skip: a pack name to leave out (the pack being validated). Also returns a warning for each
    enabled default pack that isn't on disk."""
    found, warnings = [], []
    layered = _layered("packs")
    for key in default_packs():
        cfg = layered.get(key, {})
        if not cfg.get("enabled", True) or key == skip:
            continue
        root = _pack_root(cfg, key)
        if root.is_dir():
            src = load_pack(root, key)
            if src.name != skip:
                found.append(src)
        elif "path" in cfg:
            warnings.append(f"default pack `{key}`: no directory at {tilde(root)} (its `path`), so this "
                            "pack is checked without it")
        else:
            warnings.append(f"default pack `{key}` isn't fetched yet, so this pack is checked without it; "
                            f"run `{config.command('apply')}` first, or set `path` for [{key}] in "
                            "packs.local.toml to a clone")
    return found, warnings


def skills(src: Source | None = None) -> list[Path]:
    folder = (src.root if src else config.REPO) / "skills"
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if (p / "SKILL.md").is_file())


def markdown_files(folder: str, src: Source | None = None) -> list[Path]:
    d = (src.root if src else config.REPO) / folder
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.md") if p.name != "README.md" and not p.name.endswith(".local.md"))


def items(src: Source, kind: str) -> list[Path]:
    return skills(src) if kind == "skills" else markdown_files(kind, src)


def installed_items(src: Source, kind: str) -> list[Path]:
    """items(src, kind) that this machine installs: none under the minimal profile, and never one
    that brainrc.local.toml `exclude` matches. A pattern matches the item's path in its source
    (`skills/brainrc-aws`) or that path after the pack's name (`gatework:skills/brainrc-aws`)."""
    if not config.installs("items"):
        return []
    _, exclude = config.install_profile()
    found = []
    for p in items(src, kind):
        rel = str(p.relative_to(src.root))
        if not any(fnmatch.fnmatchcase(r, pat.rstrip("/")) for pat in exclude for r in (rel, f"{src.name}:{rel}")):
            found.append(p)
    return found


def item_name(path: Path) -> str:
    return path.name if path.is_dir() else path.stem


def duplicate_packs(srcs: list[Source]) -> list[str]:
    """A name two sources share (a pack named `core` included): they'd share a hooks dir, a
    rules label, and owned hook entries, and overwrite each other on every apply."""
    def label(src: Source) -> str:  # a pack has no key under validate --pack: name its dir
        return f"[{src.key}]" if src.key else "core" if src.root == config.REPO else tilde(src.root)
    errors, seen = [], {}
    for src in srcs:
        if src.name in seen:
            errors.append(f"pack name `{src.name}` is used by both {label(seen[src.name])} and {label(src)}")
        else:
            seen[src.name] = src
    return errors


def collisions(srcs: list[Source]) -> list[str]:
    errors = []
    for kind in KINDS:
        seen: dict[str, str] = {}
        for src in srcs:
            for p in items(src, kind):
                name = item_name(p)
                if name in seen:
                    errors.append(f"{kind[:-1]} `{name}` is defined in both {seen[name]} and {src.name}")
                else:
                    seen[name] = src.name
    return errors


RULES_REFINE = "They refine the rules above and never override them."


def rule_text(path: Path) -> str:
    """A rule's text without its frontmatter (`trigger:` is for Antigravity and `alwaysApply:` for
    Cursor's plugin, which skip rules without them); harnesses brainrc writes to get the body."""
    text = path.read_text().strip()
    if text.startswith("---\n") and (end := text.find("\n---", 4)) != -1:
        text = text[end + 4:].strip()
    return text


def render_instructions(srcs: list[Source] | None = None) -> str:
    """Core rules, then one labelled block per pack in source order, then machine-local rules.

    Each group keeps filename order. Labels are a comment plus one sentence, not a heading, so
    the rules' own headings keep their structure. A core-only render has no labels.
    """
    srcs = srcs if srcs is not None else [Source("core", config.REPO)]
    names = ", ".join(s.name for s in srcs)
    parts = [f"<!-- GENERATED by brainrc from rules/*.md ({names}). Edit the source repo, not this file. -->"]
    local = []
    for i, src in enumerate(srcs):
        rules = markdown_files("rules", src)
        if rules and not src.is_core:
            parts.append(f"<!-- pack: {src.name} -->\nRules from pack {src.name}. {RULES_REFINE}")
        parts += [rule_text(p) for p in rules]
        rules_dir = (config.local_dir() if src.is_core else src.root) / "rules"
        if rules_dir.is_dir():
            local += [(p.name, i, p) for p in rules_dir.glob("*.local.md")]
    if local:
        parts.append(f"<!-- local -->\nMachine-local rules. {RULES_REFINE}")
        parts += [rule_text(p) for _, _, p in sorted(local)]
    return "\n\n".join(parts) + "\n"


def frontmatter(path: Path) -> dict[str, str]:
    """The `key: value` lines of a file's `---` frontmatter, every value a string ({} when there is
    no frontmatter or it never ends). A YAML subset: plain scalars (a ` #` comment is dropped),
    single- and double-quoted scalars, plain scalars continued on indented lines, and `|` and `>`
    block scalars with their chomping (`-`, `+`) and indentation indicators. Flow values such as
    `[a, b]` stay as written."""
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            return meta
        i += 1
        m = FM_KEY.match(line)
        if not m:
            continue
        key, value = m[1], m[2].strip()
        if block := FM_BLOCK.fullmatch(value.split(" #", 1)[0].strip()):
            body, i = _block_lines(lines, i, int(block[2] or block[4] or 0))
            meta[key] = _block_scalar(body, block[1] == "|", block[3] or block[5] or "")
        elif value[:1] in "'\"" and value:
            meta[key] = _quoted(value)
        else:
            value = value.split(" #", 1)[0].strip()
            while value and i < len(lines) and lines[i][:1] in (" ", "\t") and lines[i].strip() \
                    and not lines[i].lstrip().startswith("#"):
                value = f"{value} {lines[i].split(' #', 1)[0].strip()}".strip()
                i += 1
            meta[key] = value
    return {}  # unterminated frontmatter


FM_KEY = re.compile(r"^([^\s#][^:]*?):(?:\s+(.*)|$)")
FM_BLOCK = re.compile(r"([|>])(?:([1-9])?([+-])?|([+-])([1-9]))")
FM_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/", "0": "\0", "r": "\r"}


def _block_lines(lines: list[str], i: int, indent: int) -> tuple[list[str], int]:
    """The lines of a block scalar starting at lines[i], without their indentation, and the index
    after it. indent is the indentation indicator, or 0 to take it from the first non-blank line."""
    body = []
    while i < len(lines) and lines[i].rstrip() != "---":
        line = lines[i]
        if line.strip():
            width = len(line) - len(line.lstrip(" "))
            indent = indent or width
            if width < indent or not indent:
                break
        body.append(line[indent:] if line.strip() else "")
        i += 1
    return body, i


def _block_scalar(body: list[str], literal: bool, chomp: str) -> str:
    """YAML's `|` (keep newlines) or `>` (fold lines into spaces; blank and more-indented lines
    keep theirs), then chomping: clip one final newline, `-` strip it, `+` keep every one."""
    content = body
    while content and not content[-1]:
        content = content[:-1]
    trailing = len(body) - len(content)
    if literal:
        text = "\n".join(content)
    else:
        text, prev, prev_more = "", None, False  # prev_more: the last non-blank line was more-indented
        for line in content:
            more = line[:1] in (" ", "\t")
            if prev is None:
                text = line
            elif not line:
                text += "\n"
            elif not prev:
                text += ("\n" if more or prev_more else "") + line
            else:
                text += ("\n" if more or prev_more else " ") + line
            prev, prev_more = line, more if line else prev_more
    if not content or chomp == "-":
        return text
    return text + "\n" * (1 + trailing if chomp == "+" else 1)


def _quoted(value: str) -> str:
    """A single- or double-quoted scalar on one line ('' is a quote inside single quotes); anything
    after the closing quote (a comment) is dropped. An unclosed quote keeps the value as written."""
    quote, out, i = value[0], [], 1
    while i < len(value):
        c = value[i]
        if quote == "'" and c == "'":
            if value[i + 1:i + 2] == "'":
                out.append("'")
                i += 2
                continue
            return "".join(out)
        if quote == '"' and c == "\\" and i + 1 < len(value):
            out.append(FM_ESCAPES.get(value[i + 1], "\\" + value[i + 1]))
            i += 2
            continue
        if quote == '"' and c == '"':
            return "".join(out)
        out.append(c)
        i += 1
    return value


def _markdown_under(root: Path) -> list[Path]:
    found = []
    for dirpath, dirs, files in os.walk(root):  # does not follow symlinked dirs (skills/*/roles)
        if config.installed():  # a wheel holds copies where a checkout has links (a skill's roles/)
            dirs[:] = [d for d in dirs if d != "roles"]
        found += [Path(dirpath) / f for f in files  # a dangling link is validate's own finding
                  if f.endswith(".md") and (Path(dirpath) / f).is_file()]
    return sorted(found)
