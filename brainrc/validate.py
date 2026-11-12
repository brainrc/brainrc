"""Validation: frontmatter, references, packs, tripwires, and local tripwires (used in CI)."""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

from .mcp import check_servers
from .naming import check_core_agents, check_pack_names
from . import config
from .config import (
    ConfigError,
    EXTENSION_KEYS,
    H2,
    HOOKS_DIR_PLACEHOLDER,
    KINDS,
    KNOWN_MODELS,
    KNOWN_TOOLS,
    MODEL_ID,
    ROLES_LINK,
    REQUIRED_CONNECTOR_OPS,
    SKILL_NAME,
    _read_toml,
    check_config,
    expand,
    load_harnesses,
)
from .sources import (
    Source,
    _markdown_under,
    check_changelog,
    check_packs,
    collisions,
    core_version,
    duplicate_packs,
    frontmatter,
    item_name,
    items,
    load_pack,
    markdown_files,
    skills,
    sources,
)
from .plugin import check_plugin
from .release import check_fragments
from .tokens import check_budgets


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


# Harness built-in names a core skill must not take.
RESERVED_SKILL_NAMES = frozenset({"review", "plan", "init", "help", "status", "compact"})


def _validate_source(src: Source, agent_names: set[str], skill_names: set[str]) -> list[str]:
    errors = []
    if src.is_core:
        errors += [f"overrides/{name}/plugin.js: missing, but harnesses.toml [{name}] sets `plugin`"
                   for name, h in load_harnesses(include_disabled=True).items()
                   if "plugin" in h and not (src.root / "overrides" / name / "plugin.js").is_file()]
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

    if src.is_core:
        errors += check_core_agents(src)
        errors += [f"{src.rel(s)}: skill name `{s.name}` is reserved (a harness built-in); use a `brainrc-` name"
                   for s in skills(src) if s.name in RESERVED_SKILL_NAMES]
        errors += [f"{src.rel(r)}: missing `trigger` frontmatter (Antigravity drops the rule without it)"
                   for r in markdown_files("rules", src) if not frontmatter(r).get("trigger")]
        errors += [f"{src.rel(r)}: missing `alwaysApply: true` frontmatter (Cursor loads the rule only on request without it)"
                   for r in markdown_files("rules", src) if str(frontmatter(r).get("alwaysApply")).lower() != "true"]

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
        if meta.get("model") and meta["model"] not in KNOWN_MODELS and not MODEL_ID.match(meta["model"]):
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
    if src.is_core:
        errors += _check_local_tripwires(src)
    return errors


def _validate_pack(src: Source, agent_names: set[str], skill_names: set[str]) -> list[str]:
    where = f"{src.name}:pack.toml"
    errors = []
    errors += check_pack_names(src)
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


LOCAL_TRIPWIRES = "tripwires.local.toml"
LOCAL_FILES = ("*.local.toml", "*.local.md", "*.local.json")  # per-machine, gitignored


def _tracked_files(src: Source) -> tuple[list[Path], bool]:
    """Files git tracks in the core checkout, and whether git answered. Without git (an installed
    copy, or a checkout git can't read), every file outside dot-directories, dist/ and node_modules/,
    except the per-machine *.local.* files."""
    try:
        out = subprocess.run(["git", "-C", str(src.root), "ls-files", "-z"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return [p for p in _tripwire_files(src, ["*"])
                if not any(fnmatch.fnmatch(p.name, pat) for pat in LOCAL_FILES)], False
    return sorted(src.root / name for name in out.stdout.decode(errors="replace").split("\0") if name), True


def _check_local_tripwires(src: Source) -> list[str]:
    """Each maintainer's own forbidden terms (an employer, a client), kept out of git in
    tripwires.local.toml as `terms = [...]`: any tracked core file that contains one fails, by name or
    content, compared case-insensitively. The file itself must never be tracked."""
    path = src.root / LOCAL_TRIPWIRES
    if not path.is_file():
        return []
    files, from_git = _tracked_files(src)
    errors = [f"{LOCAL_TRIPWIRES}: is tracked by git; remove it with `git rm --cached {LOCAL_TRIPWIRES}`"
              for p in files if from_git and p == path]
    try:
        terms = _read_toml(path).get("terms", [])
    except ConfigError as e:
        return errors + [str(e)]
    if not isinstance(terms, list) or not all(isinstance(t, str) and t.strip() for t in terms):
        return errors + [f"{LOCAL_TRIPWIRES}: `terms` must be a list of non-empty strings"]
    needles = [(t, t.strip().casefold()) for t in terms]
    for p in files if needles else []:
        if p == path or not (p.is_symlink() or p.is_file()):
            continue
        rel = src.rel(p)
        errors += [f"{rel}: local tripwire: the file name contains \"{t}\" ({LOCAL_TRIPWIRES})"
                   for t, n in needles if n in rel.casefold()]
        if p.is_symlink():  # git commits the link's target path, not the file it points at
            target = os.readlink(p).casefold()
            errors += [f"{rel}: local tripwire: the link target contains \"{t}\" ({LOCAL_TRIPWIRES})"
                       for t, n in needles if n in target]
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            continue  # binary
        for lineno, line in enumerate(data.decode(errors="replace").splitlines(), 1):
            folded = line.casefold()
            errors += [f"{rel}:{lineno}: local tripwire: contains \"{t}\" ({LOCAL_TRIPWIRES})"
                       for t, n in needles if n in folded]
    return errors




ROLES_FIX = ("enable symlinks (docs/install.md, Platforms), then restore it with "
             "`git checkout -- skills/spec-agent/roles`")


def check_roles_link() -> str | None:
    """spec-agent reads its role files through roles/ -> ../../agents. A checkout without symlink
    support writes a plain file instead, and every role link breaks."""
    path = config.REPO / ROLES_LINK
    if config.installed():
        return None  # a wheel stores the link's files as copies
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


def pack_errors(srcs: list[Source]) -> list[tuple[Source, list[str]]]:
    """(pack, errors) for each pack whose own files fail what validate --pack checks; apply runs
    it before linking."""
    agent_names = {f.stem for s in srcs for f in markdown_files("agents", s)}
    skill_names = {p.name for s in srcs for p in skills(s)}
    found = [(src, _validate_source(src, agent_names, skill_names)) for src in srcs if not src.is_core]
    return [(src, errors) for src, errors in found if errors]


def cmd_validate(pack: str | None = None) -> int:
    try:
        config_warnings = check_config()
        srcs = [Source("core", config.REPO), load_pack(expand(pack).resolve())] if pack else sources()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    agent_names = {f.stem for s in srcs for f in markdown_files("agents", s)}
    skill_names = {p.name for s in srcs for p in skills(s)}
    errors = duplicate_packs(srcs) + collisions(srcs)
    if roles := check_roles_link():
        errors.append(f"{roles}; {ROLES_FIX}")
    for src in srcs:
        errors += _validate_source(src, agent_names, skill_names)
    errors += check_connectors(srcs)
    errors += check_servers(srcs)
    warnings = config_warnings
    try:
        errors += check_changelog(core_version())
        compat_errors, compat_warnings = check_packs(srcs)
        warnings += compat_warnings
        errors += compat_errors
        if not pack:
            errors += check_plugin()
            errors += check_fragments()
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
