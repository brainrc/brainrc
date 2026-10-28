"""Sources (core and packs), their items, and the rule and extension renders."""
from __future__ import annotations

import json
import os
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


def render_extensions(srcs: list[Source]) -> str:
    """The pack extension points spec-agent reads at intake, plan, and deliver."""
    packs = [s for s in srcs if not s.is_core]
    out = ["<!-- GENERATED by brainrc from each pack's pack.toml. Edit the pack, not this file. -->",
           "", "# Pack extensions", ""]
    if not packs:
        out.append("No packs enabled. Use only the built-in tables in SKILL.md.")
        return "\n".join(out) + "\n"
    out.append("Enabled packs: " + ", ".join(f"`{p.name}`" for p in packs) + ".")
    ext = {p.name: p.meta.get("extensions", {}) for p in packs}

    rows = [(p, d) for p, e in ext.items() for d in e.get("domains", [])]
    if rows:
        out += ["", "## Domains", "",
                "Extra rows for the Domains table. When both match, use the pack row's skills in",
                "addition to the built-in row's.", "",
                "| Files | Skills | Extra reviewer | Pack |", "|---|---|---|---|"]
        for pack, d in rows:
            out.append(f"| {d.get('files', '')} | {', '.join(d.get('skills', []))} | "
                       f"{d.get('reviewer', '—')} | {pack} |")

    intake = [(p, i) for p, e in ext.items() for i in e.get("intake_context", [])]
    if intake:
        out += ["", "## Intake context", "",
                "After writing `ticket.md` and before sizing, run each skill below and append its",
                "summary to `ticket.md` under `## Context` (outside the untrusted-content fence).", ""]
        out += [f"- `{i['skill']}` ({p}): {i.get('when', 'every ticket')}" for p, i in intake]

    tickets = [(p, e["ticket"]) for p, e in ext.items() if "ticket" in e]
    if tickets:
        out += ["", "## Ticket connectors", "",
                "Use the named connector for refs that match `refs`, passing it this config.", ""]
        for pack, t in tickets:
            out += [f"### {pack}", "", "```json", json.dumps(t, indent=2, sort_keys=True), "```", ""]

    checks = [(p, c) for p, e in ext.items() for c in e.get("deliver_checks", [])]
    if checks:
        out += ["", "## Deliver checks", "",
                "List these in the Deliver gate, each marked done, not applicable, or not run.",
                "Never mark a check done that did not run.", ""]
        out += [f"- ({p}) {c}" for p, c in checks]
    return "\n".join(out).rstrip() + "\n"


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return meta
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.split(" #", 1)[0].strip()
    return {}  # unterminated frontmatter


def _markdown_under(root: Path) -> list[Path]:
    found = []
    for dirpath, dirs, files in os.walk(root):  # does not follow symlinked dirs (skills/*/roles)
        dirs[:] = [d for d in dirs if Path(dirpath, d) != config.REPO / config.ROLES_LINK]  # copies, when installed
        found += [Path(dirpath) / f for f in files  # a dangling link is validate's own finding
                  if f.endswith(".md") and (Path(dirpath) / f).is_file()]
    return sorted(found)
