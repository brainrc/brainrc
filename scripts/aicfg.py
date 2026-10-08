#!/usr/bin/env python3
"""aicfg: sync this repo's skills, agents, commands, rules, and hooks into AI harnesses.

Usage:
  aicfg.py status                show what would change (default, no writes)
  aicfg.py apply                 render rules and pack extensions, create/refresh symlinks,
                                 merge settings
  aicfg.py validate [--pack DIR] check frontmatter, cross-references, packs, and tripwires
                                 (used in CI); --pack checks core plus that pack only
  aicfg.py doctor                diagnose this machine's install (read-only): stale renders,
                                 missing/broken links, broken packs, unmerged hooks; exits 1
                                 on any problem, each with its fix
  aicfg.py plugin                write the Claude Code plugin and marketplace manifests
                                 (.claude-plugin/); validate fails when they're stale
  aicfg.py tokens                estimate the context cost of every skill, agent, and command

Sources: this repo ("core", versioned by VERSION) plus any packs listed in packs.toml /
packs.local.toml. A pack is a repo with the same layout and a pack.toml (see docs/packs.md);
its `requires_core` must match VERSION, or validate fails and apply writes nothing.

Safety: never overwrites a real file or a symlink pointing outside this repo or a pack.
Those are reported as CONFLICT and left alone for you to resolve. Settings files
are merged (only entries owned by ai-config are replaced) and backed up first.
"""
from __future__ import annotations

import contextlib
import copy
import fnmatch
import io
import json
import operator
import os
import re
import shutil
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11; say so instead of a traceback
    sys.exit(f"aicfg needs Python 3.11+ (this is {sys.version.split()[0]}).")
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Hook commands under a hooks dir named ai-config or ai-config-<pack> are owned by ai-config
# and replaced on merge (so a disabled pack's hooks are removed too).
OWNED_HOOK = re.compile(r"/hooks/ai-config(?:-[a-z0-9-]+)?/")
OWNED_HOOK_MARKER = "/hooks/ai-config/"  # kept for callers that check a plain substring
# Placeholder in settings fragments, replaced with the source's hooks dir.
HOOKS_DIR_PLACEHOLDER = "{{hooks_dir}}"
BACKUPS_KEPT = 5

KNOWN_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash",
    "WebFetch", "WebSearch", "NotebookEdit", "TodoWrite",
    "AskUserQuestion", "Skill", "Agent", "TaskCreate", "TaskUpdate", "TaskList",
}
KNOWN_MODELS = {"haiku", "sonnet", "opus", "inherit"}
SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EXTENSION_KEYS = {"domains", "intake_context", "ticket", "deliver_checks"}
KINDS = ("skills", "agents", "commands")
REQUIRED_CONNECTOR_OPS = ("fetch", "comment", "transition", "link_pr")  # references/connectors.md
H2 = re.compile(r"^## +(.+)$", re.M)
CORE_VERSION = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)$")
CONSTRAINT_CLAUSE = re.compile(r"^(>=|<=|==|!=|>|<)? *([0-9]+(?:\.[0-9]+){0,2})$")
CONSTRAINT_SYNTAX = 'comma-separated clauses of >=, >, <=, <, ==, != and a version, e.g. ">=0.1, <0.2"'
CHANGELOG_VERSION = re.compile(r"^## ([0-9]+\.[0-9]+\.[0-9]+)\b", re.M)
CHANGELOG_UNRELEASED = re.compile(r"^## +unreleased\b", re.M | re.I)
COMPARE = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt,
           "==": operator.eq, "!=": operator.ne}


class ConfigError(Exception):
    pass


# ---------- config ----------

def _read_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text()) if path.is_file() else {}


def _layered(name: str) -> dict[str, dict]:
    """<name>.toml with <name>.local.toml merged over it, one table at a time."""
    config = _read_toml(REPO / f"{name}.toml")
    for key, overrides in _read_toml(REPO / f"{name}.local.toml").items():
        config.setdefault(key, {}).update(overrides)
    return config


def load_harnesses(include_disabled: bool = False) -> dict[str, dict]:
    config = _layered("harnesses")
    return {n: h for n, h in config.items() if include_disabled or h.get("enabled", True)}


def expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path)))


def tilde(path: Path) -> str:
    return str(path).replace(str(Path.home()), "~", 1)


def aicfg_home() -> Path:
    """Where apply renders rules and extensions: outside any checkout, so packaged installs can
    read them too. $AICFG_HOME, else ~/.config/ai-config."""
    if os.environ.get("AICFG_HOME"):
        return expand(os.environ["AICFG_HOME"])
    return Path.home() / ".config" / "ai-config"


def legacy_instructions() -> Path:
    """Where rules were rendered before 0.3.16; apply removes it and re-points links."""
    return REPO / "dist" / "instructions.md"


def rendered_instructions() -> Path:
    return aicfg_home() / "instructions.md"


def home_extensions_file() -> Path:
    return aicfg_home() / "extensions.md"


def extensions_file() -> Path:
    """Deprecated in-repo copy of the rendered extensions, still written for packs that read it."""
    return REPO / "skills" / "spec-agent" / "references" / "extensions.md"


def hook_command_dir(hooks_dir: str) -> str:
    """hooks_dir as written into hook commands: `~` becomes `$HOME` so the shell expands it."""
    return "$HOME" + hooks_dir[1:] if hooks_dir.startswith("~") else hooks_dir


def pack_hooks_dir(hooks_dir: str, pack: str) -> str:
    """Packs get a sibling of the core hooks dir, never a subdir (that's a symlink into core)."""
    return hooks_dir.rstrip("/") + f"-{pack}"


# ---------- sources ----------

@dataclass
class Source:
    name: str             # "core" or the pack name
    root: Path
    prefix: str = ""      # required name prefix for a pack's skills, agents, commands
    meta: dict = field(default_factory=dict)  # pack.toml

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
    meta = tomllib.loads(pack_toml.read_text())
    pack_name = str(meta.get("name", name or root.name))
    return Source(pack_name, root, str(meta.get("prefix", f"{pack_name}-")), meta)


def core_version() -> tuple[int, ...]:
    """The core version from VERSION: the contract packs pin with `requires_core`."""
    path = REPO / "VERSION"
    if not path.is_file():
        raise ConfigError("VERSION: missing (expected MAJOR.MINOR.PATCH)")
    text = path.read_text().strip()
    m = CORE_VERSION.match(text)
    if not m:
        raise ConfigError(f"VERSION: `{text}` is not MAJOR.MINOR.PATCH")
    return tuple(int(n) for n in m.groups())


def check_changelog(core: tuple[int, ...]) -> list[str]:
    """Every PR bumps VERSION and adds its entries under it: no Unreleased, newest entry = VERSION."""
    version = ".".join(map(str, core))
    path = REPO / "CHANGELOG.md"
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
                      "Every PR bumps both.")
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
    if "path" not in cfg:
        raise ConfigError(f"packs.toml [{key}]: missing `path`")
    root = expand(str(cfg["path"]))
    return root if root.is_absolute() else REPO / root


def sources(include_disabled: bool = False) -> list[Source]:
    """Core first, then packs in packs.toml order. Disabled packs are only listed (without
    reading pack.toml) when include_disabled is set, so their old links can be pruned."""
    found = [Source("core", REPO)]
    for key, cfg in _layered("packs").items():
        enabled = cfg.get("enabled", True)
        if not enabled and not include_disabled:
            continue
        root = _pack_root(cfg, key)
        found.append(load_pack(root, key) if enabled else Source(key, root))
    return found


def skills(src: Source | None = None) -> list[Path]:
    folder = (src.root if src else REPO) / "skills"
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if (p / "SKILL.md").is_file())


def markdown_files(folder: str, src: Source | None = None) -> list[Path]:
    d = (src.root if src else REPO) / folder
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.md") if p.name != "README.md" and not p.name.endswith(".local.md"))


def items(src: Source, kind: str) -> list[Path]:
    return skills(src) if kind == "skills" else markdown_files(kind, src)


def item_name(path: Path) -> str:
    return path.name if path.is_dir() else path.stem


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


def render_instructions(srcs: list[Source] | None = None) -> str:
    """Core rules, then one labelled block per pack in source order, then machine-local rules.

    Each group keeps filename order. Labels are a comment plus one sentence, not a heading, so
    the rules' own headings keep their structure. A core-only render has no labels.
    """
    srcs = srcs if srcs is not None else [Source("core", REPO)]
    names = ", ".join(s.name for s in srcs)
    parts = [f"<!-- GENERATED by ai-config from rules/*.md ({names}). Edit the source repo, not this file. -->"]
    local = []
    for i, src in enumerate(srcs):
        rules = markdown_files("rules", src)
        if rules and not src.is_core:
            parts.append(f"<!-- pack: {src.name} -->\nRules from pack {src.name}. {RULES_REFINE}")
        parts += [p.read_text().strip() for p in rules]
        rules_dir = src.root / "rules"
        if rules_dir.is_dir():
            local += [(p.name, i, p) for p in rules_dir.glob("*.local.md")]
    if local:
        parts.append(f"<!-- local -->\nMachine-local rules. {RULES_REFINE}")
        parts += [p.read_text().strip() for _, _, p in sorted(local)]
    return "\n\n".join(parts) + "\n"


def render_extensions(srcs: list[Source]) -> str:
    """The pack extension points spec-agent reads at intake, plan, and deliver."""
    packs = [s for s in srcs if not s.is_core]
    out = ["<!-- GENERATED by ai-config from each pack's pack.toml. Edit the pack, not this file. -->",
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


# ---------- planning ----------

@dataclass
class Link:
    harness: str
    dest: Path
    source: Path

    def state(self, roots: list[Path] | None = None) -> str:
        if self.dest.is_symlink():
            target = link_target(self.dest)
            if os.path.normpath(target) == os.path.normpath(self.source):
                return "ok"
            return "update" if _inside(target, roots or [REPO]) else "conflict"
        return "conflict" if self.dest.exists() else "create"


def render_fragment(fragment: Path, hooks_dir: str | None) -> dict:
    text = fragment.read_text()
    if hooks_dir:
        text = text.replace(HOOKS_DIR_PLACEHOLDER, hook_command_dir(hooks_dir))
    return json.loads(text)


@dataclass
class SettingsMerge:
    harness: str
    dest: Path
    fragments: list[tuple[Path, str | None]]  # (fragment, hooks dir) per source, in order
    extra_markers: set[str] = field(default_factory=set)

    def wanted(self) -> dict:
        hooks: dict[str, list] = {}
        for fragment, hooks_dir in self.fragments:
            for event, groups in render_fragment(fragment, hooks_dir).get("hooks", {}).items():
                hooks.setdefault(event, []).extend(groups)
        return {"hooks": hooks}

    def markers(self) -> set[str]:
        dirs = {hd for _, hd in self.fragments if hd} | self.extra_markers
        return {hook_command_dir(d).rstrip("/") + "/" for d in dirs}


def link_target(link: Path) -> Path:
    """Where a symlink points, with relative targets resolved against the link's directory."""
    target = Path(os.readlink(link))
    return target if target.is_absolute() else link.parent / target


def _inside(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def _inside_repo(path: Path) -> bool:
    return _inside(path, [REPO])


def _managed_target(target: Path, roots: list[Path]) -> bool:
    """True if target is a path aicfg itself links to inside one of the source roots."""
    t = Path(os.path.abspath(target)).resolve()
    if t == rendered_instructions().resolve():
        return True
    for root in (r.resolve() for r in roots):
        if t.parent in {root / k for k in KINDS}:
            return True
        if t == root / "dist" / "instructions.md":  # pre-0.3.16 render location
            return True
        if t.name == "hooks" and t.parent.parent == root / "overrides":
            return True
    return False


def plan(srcs: list[Source] | None = None, every_src: list[Source] | None = None
         ) -> tuple[list[Link], list[Path], list[SettingsMerge]]:
    srcs = srcs if srcs is not None else sources()
    every_src = every_src if every_src is not None else sources(include_disabled=True)
    roots = [s.root for s in every_src]
    links: list[Link] = []
    merges: list[SettingsMerge] = []
    for name, h in load_harnesses().items():
        for kind in KINDS:
            if kind in h:
                d = expand(h[kind])
                links += [Link(name, d / p.name, p) for src in srcs for p in items(src, kind)]
        if "instructions" in h:
            links.append(Link(name, expand(h["instructions"]), rendered_instructions()))
        fragments: list[tuple[Path, str | None]] = []
        for src in srcs:
            hooks = src.root / "overrides" / name / "hooks"
            hooks_dir = None
            if "hooks_dir" in h:
                hooks_dir = h["hooks_dir"] if src.is_core else pack_hooks_dir(h["hooks_dir"], src.name)
                if src.is_core or hooks.is_dir():
                    links.append(Link(name, expand(hooks_dir), hooks))
            fragment = src.root / "overrides" / name / "settings.fragment.json"
            if fragment.is_file():
                fragments.append((fragment, hooks_dir))
        if "settings" in h and fragments:
            known = {pack_hooks_dir(h["hooks_dir"], s.name) for s in every_src if "hooks_dir" in h}
            merges.append(SettingsMerge(name, expand(h["settings"]), fragments, known))
    # A disabled harness keeps its settings file, so take ai-config's hooks back out of it:
    # merging no fragments removes only the groups ai-config owns.
    enabled = load_harnesses()
    for name, h in load_harnesses(include_disabled=True).items():
        if name not in enabled and "settings" in h:
            known = set()
            if "hooks_dir" in h:
                known = {h["hooks_dir"]} | {pack_hooks_dir(h["hooks_dir"], s.name) for s in every_src}
            merges.append(SettingsMerge(name, expand(h["settings"]), [], known))

    # Stale: links aicfg made earlier that it wouldn't make now (removed items, disabled packs,
    # disabled harnesses). Only symlinks pointing at a path aicfg links to are touched.
    wanted = {link.dest for link in links}
    candidates: set[Path] = set()
    for h in load_harnesses(include_disabled=True).values():
        for kind in KINDS:
            d = expand(h[kind]) if kind in h else None
            if d and d.is_dir():
                candidates.update(d.iterdir())
        if "instructions" in h:
            candidates.add(expand(h["instructions"]))
        if "hooks_dir" in h:
            candidates.add(expand(h["hooks_dir"]))
            candidates.update(expand(pack_hooks_dir(h["hooks_dir"], s.name)) for s in every_src)
    stale = sorted(p for p in candidates
                   if p.is_symlink() and p not in wanted and _managed_target(link_target(p), roots))
    return links, stale, merges


# ---------- settings merge ----------

def _owned(group: dict, markers: set[str] = frozenset()) -> bool:
    for h in group.get("hooks", []):
        command = str(h.get("command", ""))
        if OWNED_HOOK.search(command) or any(m in command for m in markers):
            return True
    return False


def merge_settings(current: dict, fragment: dict, markers: set[str] = frozenset()) -> dict:
    """Return current with ai-config's hook groups replaced by the fragment's.

    Hook groups owned by other tools/plugins are kept in place and order. Only the
    `hooks` key of the fragment is merged; other settings stay under user control.
    """
    merged = copy.deepcopy(current)
    hooks = merged.setdefault("hooks", {})
    wanted = fragment.get("hooks", {})
    for event in set(hooks) | set(wanted):
        kept = [g for g in hooks.get(event, []) if not _owned(g, markers)]
        groups = kept + copy.deepcopy(wanted.get(event, []))
        if groups:
            hooks[event] = groups
        else:
            hooks.pop(event, None)
    if not hooks and current.get("hooks") != {}:  # drop the key ai-config emptied, keep a user's own {}
        merged.pop("hooks")
    return merged


def settings_change(m: SettingsMerge) -> tuple[str, dict | None]:
    """Return (state, merged) where state is ok | merge | conflict."""
    try:
        current = json.loads(m.dest.read_text()) if m.dest.exists() else {}
    except json.JSONDecodeError:
        return "conflict", None
    merged = merge_settings(current, m.wanted(), m.markers())
    return ("ok" if merged == current else "merge"), merged


def write_settings(dest: Path, merged: dict) -> None:
    """Back up, prune old backups, then replace atomically so a crash never leaves half a file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(dest, dest.with_name(f"{dest.name}.bak-aicfg-{stamp}"))
        backups = sorted(dest.parent.glob(f"{dest.name}.bak-aicfg-*"))
        for old in backups[:-BACKUPS_KEPT]:
            old.unlink()
    tmp = dest.with_name(f".{dest.name}.aicfg-tmp")
    tmp.write_text(json.dumps(merged, indent=2) + "\n")
    os.replace(tmp, dest)


# ---------- commands ----------

def cmd_sync(apply: bool) -> int:
    try:
        srcs = sources()
        roots = [s.root for s in sources(include_disabled=True)]
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    clashes = collisions(srcs)
    if clashes:
        for c in clashes:
            print(f"ERROR {c}")
        print("\nNothing written. Rename one of each pair, then re-run.")
        return 1
    try:
        incompatible, warnings = check_packs(srcs)
    except ConfigError as e:
        incompatible, warnings = [str(e)], []
    for w in warnings:
        print(f"WARN {w}")
    if incompatible:
        for e in incompatible:
            print(f"ERROR {e}")
        print("\nNothing written. Update the pack or core (see CHANGELOG.md), or disable the pack.")
        return 1

    if apply:
        rendered = rendered_instructions()
        rendered.parent.mkdir(parents=True, exist_ok=True)
        rendered.write_text(render_instructions(srcs))
        extensions = render_extensions(srcs)
        home_extensions_file().write_text(extensions)
        if extensions_file().parent.is_dir():
            extensions_file().write_text(extensions)
        if legacy_instructions().is_file():
            legacy_instructions().unlink()

    links, stale, merges = plan(srcs)
    conflicts = changes = 0
    for link in links:
        state = link.state(roots)
        if state == "ok":
            continue
        print(f"{state.upper():9} {link.harness:9} {tilde(link.dest)}")
        if state == "conflict":
            conflicts += 1
            continue
        changes += 1
        if apply:
            link.dest.parent.mkdir(parents=True, exist_ok=True)
            if link.dest.is_symlink():
                link.dest.unlink()
            link.dest.symlink_to(link.source)
    for p in stale:
        changes += 1
        print(f"{'PRUNE':9} {'':9} {tilde(p)}")
        if apply:
            p.unlink()
    for m in merges:
        state, merged = settings_change(m)
        if state == "ok":
            continue
        print(f"{state.upper():9} {m.harness:9} {tilde(m.dest)}"
              + ("  (invalid JSON, fix by hand)" if state == "conflict" else "  (hooks)"))
        if state == "conflict":
            conflicts += 1
            continue
        changes += 1
        if apply:
            write_settings(m.dest, merged)

    if not changes and not conflicts:
        print("Everything in sync.")
    elif not apply and changes:
        print("\nDry run. Run `apply` to write.")
    if conflicts:
        print(f"\n{conflicts} conflict(s): existing files not managed by this repo. "
              "Move them into the repo (or delete them), then re-run.")
    return 1 if conflicts else 0


# ---------- validation ----------

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
    for dirpath, _dirs, files in os.walk(root):  # does not follow symlinked dirs (skills/*/roles)
        found += [Path(dirpath) / f for f in files if f.endswith(".md")]
    return sorted(found)


FENCE = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
AGENT_TAG = re.compile(r"\[agent:\s*([a-z0-9-]+)\]")
SKILL_MENTION = re.compile(r"`([a-z0-9-]+)` skill")


def _check_references(src: Source, path: Path, agent_names: set[str], skill_names: set[str]) -> list[str]:
    rel = src.rel(path)
    text = FENCE.sub("", path.read_text())
    errors = []
    for target in MD_LINK.findall(text):
        if re.match(r"^[a-z]+:", target) or target.startswith("#") or "<" in target:
            continue
        if not (path.parent / target.split("#", 1)[0]).exists():
            errors.append(f"{rel}: broken link `{target}`")
    errors += [f"{rel}: unknown agent `{a}`" for a in AGENT_TAG.findall(text) if a not in agent_names]
    errors += [f"{rel}: unknown skill `{s}`" for s in SKILL_MENTION.findall(text) if s not in skill_names]
    return errors


def _validate_source(src: Source, agent_names: set[str], skill_names: set[str]) -> list[str]:
    errors = []
    for s in skills(src):
        rel = src.rel(s)
        meta = frontmatter(s / "SKILL.md")
        if meta.get("name") != s.name:
            errors.append(f"{rel}/SKILL.md: `name` must equal the directory name")
        if not SKILL_NAME.match(s.name) or len(s.name) > 64:
            errors.append(f"{rel}: name must be lowercase-hyphenated, 64 chars max")
        description = meta.get("description", "")
        if not description:
            errors.append(f"{rel}/SKILL.md: missing `description`")
        elif len(description) > 1024:
            errors.append(f"{rel}/SKILL.md: `description` over 1024 chars")
        for dirpath, dirs, files in os.walk(s):
            for entry in dirs + files:
                p = Path(dirpath) / entry
                if p.is_symlink() and not p.exists():
                    errors.append(f"{src.rel(p)}: dangling symlink")
        for md in _markdown_under(s):
            errors += _check_references(src, md, agent_names, skill_names)

    for f in markdown_files("agents", src):
        rel = src.rel(f)
        meta = frontmatter(f)
        if meta.get("name") != f.stem:
            errors.append(f"{rel}: `name` must equal the file name")
        if not meta.get("description"):
            errors.append(f"{rel}: missing `description`")
        tools = {t.strip() for t in meta.get("tools", "").split(",") if t.strip()}
        errors += [f"{rel}: unknown tool `{t}`"
                   for t in sorted(tools - KNOWN_TOOLS) if not t.startswith("mcp__")]
        if meta.get("model") and meta["model"] not in KNOWN_MODELS:
            errors.append(f"{rel}: unknown model `{meta['model']}`")
        errors += _check_references(src, f, agent_names, skill_names)

    for f in markdown_files("commands", src):
        if not frontmatter(f).get("description"):
            errors.append(f"{src.rel(f)}: missing `description`")
        errors += _check_references(src, f, agent_names, skill_names)

    overrides = src.root / "overrides"
    for fragment in sorted(overrides.glob("*/settings.fragment.json")) if overrides.is_dir() else []:
        try:
            json.loads(fragment.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{src.rel(fragment)}: invalid JSON ({e})")
        harness = load_harnesses(include_disabled=True).get(fragment.parent.name, {})
        if HOOKS_DIR_PLACEHOLDER in fragment.read_text() and "hooks_dir" not in harness:
            errors.append(f"{src.rel(fragment)}: uses {HOOKS_DIR_PLACEHOLDER} but harnesses.toml "
                          f"[{fragment.parent.name}] has no hooks_dir")

    if not src.is_core:
        errors += _validate_pack(src, agent_names, skill_names)
    errors += _check_tripwires(src)
    return errors


def _validate_pack(src: Source, agent_names: set[str], skill_names: set[str]) -> list[str]:
    where = f"{src.name}:pack.toml"
    errors = []
    if not SKILL_NAME.match(src.name):
        errors.append(f"{where}: `name` must be lowercase-hyphenated")
    if not src.prefix.endswith("-") or not SKILL_NAME.match(src.prefix[:-1]):
        errors.append(f"{where}: `prefix` must be lowercase-hyphenated and end with '-'")
    for kind in KINDS:
        for p in items(src, kind):
            if not item_name(p).startswith(src.prefix):
                errors.append(f"{src.rel(p)}: pack {kind} must start with `{src.prefix}`")
    ext = src.meta.get("extensions", {})
    errors += [f"{where}: unknown extension `{k}`" for k in sorted(set(ext) - EXTENSION_KEYS)]
    for d in ext.get("domains", []):
        if not d.get("files") or not d.get("skills"):
            errors.append(f"{where}: each extensions.domains entry needs `files` and `skills`")
        errors += [f"{where}: domains names unknown skill `{s}`" for s in d.get("skills", []) if s not in skill_names]
        if d.get("reviewer") and d["reviewer"] not in agent_names:
            errors.append(f"{where}: domains names unknown reviewer `{d['reviewer']}`")
    for i in ext.get("intake_context", []):
        if i.get("skill") not in skill_names:
            errors.append(f"{where}: intake_context names unknown skill `{i.get('skill')}`")
    ticket = ext.get("ticket")
    if ticket is not None:
        if ticket.get("connector") not in skill_names:
            errors.append(f"{where}: ticket.connector names unknown skill `{ticket.get('connector')}`")
        if not ticket.get("refs"):
            errors.append(f"{where}: ticket needs `refs` (the ticket refs it handles, e.g. \"PROJ-*\")")
    if not all(isinstance(c, str) for c in ext.get("deliver_checks", [])):
        errors.append(f"{where}: deliver_checks must be a list of strings")
    return errors


def _tripwire_files(src: Source, patterns: list[str]) -> list[Path]:
    found = []
    for dirpath, dirs, files in os.walk(src.root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("dist", "node_modules")]
        for f in files:
            p = Path(dirpath) / f
            rel = str(p.relative_to(src.root))
            if any(fnmatch.fnmatch(rel, pat) for pat in patterns):
                found.append(p)
    return sorted(found)


def _check_tripwires(src: Source) -> list[str]:
    """Stale facts that must not come back: tripwires.toml [[tripwire]] pattern/message/allow/paths."""
    errors = []
    for t in _read_toml(src.root / "tripwires.toml").get("tripwire", []):
        tid = t.get("id", "?")
        try:
            pattern = re.compile(t["pattern"])
            allow = re.compile(t["allow"]) if t.get("allow") else None
        except (KeyError, re.error) as e:
            errors.append(f"{src.name}:tripwires.toml: tripwire {tid} is invalid ({e})")
            continue
        exclude = t.get("exclude", ["tripwires.toml"])
        for p in _tripwire_files(src, t.get("paths", ["*.md"])):
            rel = str(p.relative_to(src.root))
            if any(fnmatch.fnmatch(rel, pat) for pat in exclude):
                continue
            for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if pattern.search(line) and not (allow and allow.search(line)):
                    errors.append(f"{src.rel(p)}:{n}: tripwire {tid}: {t.get('message', t['pattern'])}")
    return errors


ROLES_LINK = Path("skills/spec-agent/roles")


ROLES_FIX = ("enable symlinks (README, Platforms), then restore it with "
             "`git checkout -- skills/spec-agent/roles`")


def check_roles_link() -> str | None:
    """spec-agent reads its role files through roles/ -> ../../agents. A checkout without symlink
    support writes a plain file instead, and every role link breaks."""
    path = REPO / ROLES_LINK
    if not path.is_symlink() and not path.exists():
        return None  # not this repo's layout (e.g. a pack)
    if path.is_symlink() and os.readlink(path) == "../../agents":
        return None
    found = f"a link to {os.readlink(path)}" if path.is_symlink() else "a plain file"
    return f"{ROLES_LINK} must be a symlink to ../../agents but is {found} (cloned without symlink support?)"


def check_connectors(srcs: list[Source]) -> list[str]:
    """Core `ticket-*` skills and pack `[extensions.ticket]` connectors need a `##` heading naming
    each required operation. One heading may name several (`## comment / transition / link_pr`)."""
    found = {s.name: (src, s) for src in srcs for s in skills(src)}
    names = {n for n, (src, _) in found.items() if src.is_core and n.startswith("ticket-")}
    names |= {src.meta.get("extensions", {}).get("ticket", {}).get("connector") for src in srcs}
    errors = []
    for name in sorted(n for n in names if n in found):
        src, skill = found[name]
        headings = " ".join(H2.findall((skill / "SKILL.md").read_text()))
        missing = [op for op in REQUIRED_CONNECTOR_OPS if not re.search(rf"\b{op}\b", headings)]
        if missing:
            errors.append(f"{src.rel(skill)}/SKILL.md: connector missing `##` sections for "
                          f"{', '.join(missing)} (see skills/spec-agent/references/connectors.md)")
    return errors


def cmd_validate(pack: str | None = None) -> int:
    try:
        srcs = [Source("core", REPO), load_pack(expand(pack).resolve())] if pack else sources()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    agent_names = {f.stem for s in srcs for f in markdown_files("agents", s)}
    skill_names = {p.name for s in srcs for p in skills(s)}
    errors = collisions(srcs)
    if roles := check_roles_link():
        errors.append(f"{roles}; {ROLES_FIX}")
    for src in srcs:
        errors += _validate_source(src, agent_names, skill_names)
    errors += check_connectors(srcs)
    warnings = []
    try:
        errors += check_changelog(core_version())
        compat_errors, warnings = check_packs(srcs)
        errors += compat_errors
        if not pack:
            errors += check_plugin()
        budget_errors, budget_warnings = check_budgets(srcs)
        errors += budget_errors
        warnings += budget_warnings
    except ConfigError as e:
        errors.append(str(e))

    for w in warnings:
        print(f"WARN {w}")
    for e in errors:
        print(f"ERROR {e}")
    commands = sum(len(markdown_files("commands", s)) for s in srcs)
    packs = [s.name for s in srcs if not s.is_core]
    counts = (f"{len(skill_names)} skills, {len(agent_names)} agents, {commands} commands"
              + (f" (packs: {', '.join(packs)})" if packs else ""))
    print(f"{'FAILED' if errors else 'OK'}: {counts}")
    return 1 if errors else 0


# ---------- doctor ----------

APPLY = "python3 scripts/aicfg.py apply"
Finding = tuple[str, str, str]  # (FAIL | WARN, what is wrong, how to fix it)


def _doctor_sources() -> tuple[list[Source], list[Source], list[Finding]]:
    """(sources apply would use, every source root incl. disabled or broken packs, findings).
    Each pack is checked on its own, so one broken pack doesn't hide the rest."""
    srcs, every_src, found = [Source("core", REPO)], [Source("core", REPO)], []
    try:
        core = core_version()
        packs = _layered("packs")
    except (ConfigError, tomllib.TOMLDecodeError) as e:
        return srcs, every_src, [("FAIL", str(e), "fix VERSION or packs.toml / packs.local.toml")]
    disable = "or set `enabled = false` for it in packs.local.toml"
    for key, cfg in packs.items():
        try:
            root = _pack_root(cfg, key)
        except ConfigError as e:
            found.append(("FAIL", str(e), f"add `path` to [{key}], {disable}"))
            continue
        if not cfg.get("enabled", True):
            every_src.append(Source(key, root))
            continue
        try:
            src = load_pack(root, key)
        except ConfigError as e:
            every_src.append(Source(key, root))
            found.append(("FAIL", str(e),
                          f"fix `path` for [{key}] in packs.toml / packs.local.toml, {disable}"))
            continue
        every_src.append(src)
        errors, _ = pack_compat(src, core)
        if errors:
            fix = f"update the pack or core (see CHANGELOG.md), {disable}"
            found += [("FAIL", e, fix) for e in errors]
            continue
        with contextlib.redirect_stdout(io.StringIO()):
            failed = cmd_validate(str(root))
        if failed:
            found.append(("FAIL", f"pack {src.name}: validate --pack fails",
                          f"python3 scripts/aicfg.py validate --pack {tilde(root)}"))
        srcs.append(src)
    found += [("FAIL", c, "rename one of the pair, then apply") for c in collisions(srcs)]
    return srcs, every_src, found


def _render_findings(srcs: list[Source]) -> list[Finding]:
    found = []
    targets = [(rendered_instructions(), lambda: render_instructions(srcs)),
               (home_extensions_file(), lambda: render_extensions(srcs))]
    if extensions_file().parent.is_dir():
        targets.append((extensions_file(), lambda: render_extensions(srcs)))
    for path, render in targets:
        rel = tilde(path) if not path.is_relative_to(REPO) else str(path.relative_to(REPO))
        if not path.is_file():
            found.append(("FAIL", f"{rel} has not been rendered", APPLY))
        elif path.read_text() != render():
            found.append(("FAIL", f"{rel} is stale (sources changed since the last apply)", APPLY))
    return found


def _link_finding(link: Link, roots: list[Path]) -> Finding | None:
    state, dest = link.state(roots), tilde(link.dest)
    if state == "create":
        return "FAIL", f"{link.harness}: {dest} is missing", APPLY
    if state == "update":
        return "FAIL", f"{link.harness}: {dest} points at the wrong item", APPLY
    if state == "ok":
        return None
    if not link.dest.is_symlink():
        return ("FAIL", f"{link.harness}: {dest} is a real file, not a link",
                f"move it into the repo or a pack (or delete it), then {APPLY}")
    target = link_target(link.dest)
    if not target.exists():
        return ("FAIL", f"{link.harness}: {dest} is a broken link to {tilde(target)} (repo moved?)",
                f"rm {dest} && {APPLY}")
    return ("FAIL", f"{link.harness}: {dest} links to {tilde(target)}, outside ai-config and its packs",
            f"move that into a pack (or delete the link), then {APPLY}")


def doctor_findings() -> list[Finding]:
    """Everything wrong with this machine's install, each with its fix. Writes nothing."""
    srcs, every_src, found = _doctor_sources()
    if roles := check_roles_link():
        found.append(("FAIL", roles, ROLES_FIX))
    found += _render_findings(srcs)
    roots = [s.root for s in every_src]
    links, stale, merges = plan(srcs, every_src)

    skipped = set()
    for name, h in load_harnesses().items():
        key = next((k for k in ("instructions", "skills") if k in h), None)
        home = expand(h[key]).parent if key else None
        if home and not home.is_dir():
            skipped.add(name)
            found.append(("WARN", f"{name}: {tilde(home)} doesn't exist (not installed?)",
                          f"add `[{name}] enabled = false` to harnesses.local.toml, or install it"))
    missing: dict[str, list[Link]] = {}
    for link in links:
        if link.harness in skipped:
            continue
        if link.state(roots) == "create":
            missing.setdefault(link.harness, []).append(link)
        elif f := _link_finding(link, roots):
            found.append(f)
    for name, group in missing.items():  # a never-applied harness is one line, not dozens
        if len(group) > 3:
            found.append(("FAIL", f"{name}: {len(group)} links are missing, e.g. {tilde(group[0].dest)}",
                          APPLY))
        else:
            found += [_link_finding(link, roots) for link in group]
    found += [("FAIL", f"{tilde(p)} is a stale link ai-config no longer makes", f"{APPLY} (prunes it)")
              for p in stale]

    # Broken links aicfg doesn't manage, in the directories it links into.
    known = {link.dest for link in links} | set(stale)
    for name, h in load_harnesses().items():
        for kind in KINDS:
            d = expand(h[kind]) if kind in h and name not in skipped else None
            for p in sorted(d.iterdir()) if d and d.is_dir() else []:
                if p.is_symlink() and not p.exists() and p not in known:
                    found.append(("WARN", f"{name}: {tilde(p)} is a broken link not made by ai-config",
                                  f"rm {tilde(p)}"))

    for m in merges:
        if m.harness in skipped:
            continue
        state, _ = settings_change(m)
        if state == "merge" and not m.fragments:
            found.append(("FAIL", f"{tilde(m.dest)} has ai-config's hooks but {m.harness} is disabled",
                          f"{APPLY} (removes them)"))
        elif state == "merge":
            found.append(("FAIL", f"{m.harness}: {tilde(m.dest)} is missing ai-config's hooks", APPLY))
        elif state == "conflict":
            found.append(("FAIL", f"{m.harness}: {tilde(m.dest)} is invalid JSON",
                          f"fix it by hand, then {APPLY}"))
    return found


def cmd_doctor() -> int:
    findings = doctor_findings()
    for level, what, fix in findings:
        print(f"{level} {what}\n     fix: {fix}")
    fails = sum(level == "FAIL" for level, _, _ in findings)
    if findings:
        print(f"\n{fails} problem(s), {len(findings) - fails} warning(s). "
              "More help: docs/troubleshooting.md")
    else:
        print("No problems found.")
    return 1 if fails else 0


# ---------- plugin ----------

PLUGIN_DIR = ".claude-plugin"


PLUGIN_NAME = "ai-config"
PLUGIN_AUTHOR = {"name": "ai-config contributors"}
PLUGIN_DESCRIPTION = ("Skills, agents, commands, and guard hooks for spec-driven work: spec-agent "
                      "takes a ticket to a reviewed PR through approval gates.")


def plugin_manifests() -> dict[str, str]:
    """The Claude Code plugin and marketplace manifests for core, built from the repo.
    The repo root is the plugin (default skills/, agents/, commands/ folders) and the marketplace."""
    version = ".".join(map(str, core_version()))
    hooks_dir = "${CLAUDE_PLUGIN_ROOT}/overrides/claude/hooks"
    hooks = render_fragment(REPO / "overrides" / "claude" / "settings.fragment.json", hooks_dir)["hooks"]
    plugin = {"name": PLUGIN_NAME, "version": version, "description": PLUGIN_DESCRIPTION,
              "author": PLUGIN_AUTHOR, "license": "MIT", "hooks": hooks}
    market = {"name": PLUGIN_NAME, "owner": PLUGIN_AUTHOR, "description": PLUGIN_DESCRIPTION,
              "plugins": [{"name": PLUGIN_NAME, "source": ".", "description": PLUGIN_DESCRIPTION,
                           "version": version}]}
    return {f"{PLUGIN_DIR}/{name}": json.dumps(data, indent=2) + "\n"
            for name, data in (("plugin.json", plugin), ("marketplace.json", market))}


def check_plugin() -> list[str]:
    """Only where the repo publishes a plugin (has .claude-plugin/), as core does."""
    if not (REPO / PLUGIN_DIR).is_dir():
        return []
    errors = []
    for rel, text in plugin_manifests().items():
        path = REPO / rel
        if not path.is_file():
            errors.append(f"{rel}: missing; run `python3 scripts/aicfg.py plugin`")
        elif path.read_text() != text:
            errors.append(f"{rel}: stale (VERSION, hooks, or the fragment changed); "
                          "run `python3 scripts/aicfg.py plugin`")
    return errors


def cmd_plugin() -> int:
    """Write the Claude Code plugin manifests; they're committed so GitHub installs work."""
    try:
        manifests = plugin_manifests()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    changed = False
    for rel, text in manifests.items():
        path = REPO / rel
        if path.is_file() and path.read_text() == text:
            continue
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
        print(f"WROTE {rel}")
        changed = True
    if not changed:
        print("Plugin manifests up to date.")
    return 0


# ---------- tokens ----------

def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4  # ~4 chars per token; good enough to compare sizes


CORE_ALWAYS_BUDGET = 3000     # tokens core may load into every session (rules + descriptions)
PACK_WARN_TOKENS = 1000       # a pack without max_always_tokens gets a warning above this
DESCRIPTION_WARN_TOKENS = 100


def _description_tokens(path: Path) -> int:
    return estimate_tokens(frontmatter(path).get("description", ""))


def always_tokens(src: Source) -> tuple[int, list[tuple[int, str]]]:
    """What a source loads into every session: its rules, and each item's description."""
    items = [(estimate_tokens(p.read_text().strip()), src.rel(p)) for p in markdown_files("rules", src)]
    items += [(_description_tokens(s / "SKILL.md"), src.rel(s)) for s in skills(src)]
    items += [(_description_tokens(f), src.rel(f)) for kind in ("agents", "commands")
              for f in markdown_files(kind, src)]
    return sum(n for n, _ in items), items


def source_budget(src: Source) -> int | None:
    return CORE_ALWAYS_BUDGET if src.is_core else src.meta.get("max_always_tokens")


def check_budgets(srcs: list[Source]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for src in srcs:
        total, items = always_tokens(src)
        biggest = ", ".join(f"{label} {n}" for n, label in sorted(items, reverse=True)[:3])
        budget = source_budget(src)
        if budget is not None and total > budget:
            errors.append(f"{src.name}: ~{total} always-loaded tokens, budget {budget} (biggest: {biggest})")
        elif budget is None and total > PACK_WARN_TOKENS:
            warnings.append(f"{src.name}: ~{total} always-loaded tokens and no `max_always_tokens` in "
                            f"pack.toml (biggest: {biggest})")
        for f in [s / "SKILL.md" for s in skills(src)] + [f for k in ("agents", "commands")
                                                         for f in markdown_files(k, src)]:
            n = _description_tokens(f)
            if n > DESCRIPTION_WARN_TOKENS:
                label = src.rel(f.parent if f.name == "SKILL.md" else f)
                warnings.append(f"{label}: description is ~{n} tokens (over {DESCRIPTION_WARN_TOKENS})")
    return errors, warnings


def cmd_tokens() -> int:
    """Context cost per item. `always` loads in every session; `on use` only when triggered."""
    try:
        srcs = sources()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    rows: list[tuple[int, int, str]] = []  # (on-use tokens, always tokens, label)
    for src in srcs:
        tag = "" if src.is_core else f"{src.name}:"
        for s in skills(src):
            body = estimate_tokens((s / "SKILL.md").read_text())
            refs = sum(estimate_tokens(p.read_text()) for p in _markdown_under(s) if p.name != "SKILL.md")
            description = estimate_tokens(frontmatter(s / "SKILL.md").get("description", ""))
            rows.append((body + refs, description, f"{tag}skills/{s.name} (SKILL.md {body}, refs {refs})"))
        for kind in ("agents", "commands"):
            for f in markdown_files(kind, src):
                description = estimate_tokens(frontmatter(f).get("description", ""))
                rows.append((estimate_tokens(f.read_text()), description, f"{tag}{kind}/{f.name}"))
    instructions = estimate_tokens(render_instructions(srcs))
    print(f"{'on use':>7} {'always':>7}  item")
    for on_use, always, label in sorted(rows, reverse=True):
        print(f"{on_use:7} {always:7}  {label}")
    always_total = instructions + sum(r[1] for r in rows)
    print(f"\nAlways loaded: ~{always_total} tokens (rules {instructions}, descriptions "
          f"{always_total - instructions}). On use: ~{sum(r[0] for r in rows)} tokens if everything loads.")
    for src in srcs:
        budget = source_budget(src)
        print(f"{src.name}: ~{always_tokens(src)[0]} / {budget if budget is not None else 'no budget'} "
              "always-loaded tokens")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd in ("status", "apply") and len(argv) <= 2:
        return cmd_sync(apply=cmd == "apply")
    if cmd == "validate":
        if len(argv) == 2:
            return cmd_validate()
        if len(argv) == 4 and argv[2] == "--pack":
            return cmd_validate(argv[3])
    if cmd == "plugin" and len(argv) == 2:
        return cmd_plugin()
    if cmd == "doctor" and len(argv) == 2:
        return cmd_doctor()
    if cmd == "tokens" and len(argv) == 2:
        return cmd_tokens()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
