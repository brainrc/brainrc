"""Validation: frontmatter, references, packs, tripwires, and local tripwires (used in CI)."""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

from .mcp import check_servers
from .naming import check_pack_names, unprefixed_ok
from .packs import pinned_defaults
from .plugins import extension_errors, extension_warnings, plugin_errors, validators
from . import config, connectors, copies, gitlinks, guard, packtests, schema
from . import scope as pack_scope
from .config import (
    ConfigError,
    HOOKS_DIR_PLACEHOLDER,
    KINDS,
    KNOWN_MODELS,
    KNOWN_TOOLS,
    MODEL_ID,
    SKILL_NAME,
    _read_toml,
    check_config,
    did_you_mean,
    expand,
    key_line,
    line_of,
    load_harnesses,
    tilde,
)
from .sources import (
    Source,
    _markdown_under,
    default_sources,
    check_changelog,
    check_packs,
    compat_deprecations,
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


# A skill named in prose, without backticks: "the acme-deploy skill" (#137). Only a hyphenated name
# whose first part is the pack's prefix, or one two known skills share, counts, so "the write-up
# skill" and "the acme-specific skill set" stay prose.
PROSE_SKILL = re.compile(r"\b(?i:the)\s+([a-z0-9]+(?:-[a-z0-9]+)+)\s+skill(?![-\w]|\s+(?:sets?|trees?|levels?)\b)")


def _check_references(src: Source, path: Path, agent_names: set[str], skill_names: set[str],
                      links: bool = True, tags: bool = True, prose: bool = False) -> list[str]:
    """Broken relative links, unknown `[agent: x]` tags and skills named as "`x` skill" (tags), and,
    with prose, unknown skills named as "the x skill"."""
    rel = src.rel(path)
    text = FENCE.sub("", path.read_text())
    errors = []
    for target in MD_LINK.findall(text) if links else []:
        if re.match(r"^[a-z]+:", target) or target.startswith("#") or "<" in target:
            continue
        local = _unquote(target.split("#", 1)[0])
        # "/docs/x.md" is relative to the pack's (or core's) root, as GitHub reads it.
        at = (src.root / local.lstrip("/")) if local.startswith("/") else (path.parent / local)
        if at.exists():
            continue
        if (via := gitlinks.resolve(at)) != at and via.exists():  # through git's stand-in for a link
            if copies.copying():  # apply copies what the stand-in points to
                continue
            errors.append(f"{rel}: link `{target}` goes through a link git checked out as a plain file "
                          "(symlinks off); set link_mode = \"copy\", or clone the pack again with "
                          "core.symlinks on")
            continue
        errors.append(f"{rel}: broken link `{target}`")
    if tags:
        errors += [f"{rel}: unknown agent `{a}`" for a in AGENT_TAG.findall(text) if a not in agent_names]
        errors += [f"{rel}: unknown skill `{s}`" for s in SKILL_MENTION.findall(text) if s not in skill_names]
    if prose:
        firsts = [n.split("-", 1)[0] for n in skill_names]
        heads = {h for h in firsts if firsts.count(h) > 1} | {src.prefix.split("-", 1)[0]} - {""}
        errors += [f"{rel}: unknown skill `{s}` (named as \"the {s} skill\")" for s in PROSE_SKILL.findall(text)
                   if s not in skill_names and s.split("-", 1)[0] in heads]
    return errors


def _unquote(link: str) -> str:
    """A link's %XX escapes decoded (`my%20notes.md` -> `my notes.md`); no urllib, which the
    no-network test keeps out of brainrc/."""
    return re.sub(rb"%([0-9A-Fa-f]{2})", lambda m: bytes([int(m[1], 16)]), link.encode()).decode(errors="replace")


def _docs(src: Source) -> list[Path]:
    """A pack's README.md and docs/**/*.md, whose links and references validate checks too."""
    readme = [src.root / name for name in ("README.md",) if (src.root / name).is_file()]
    return readme + (_markdown_under(src.root / "docs") if (src.root / "docs").is_dir() else [])


def coverage_findings(src: Source, agent_names: set[str], skill_names: set[str]) -> tuple[list[str], list[str]]:
    """(errors, warnings) from what validate checks beyond what apply refuses (#137): skills named in
    prose everywhere, references in rules, and links in a pack's README.md and docs/**. A relative
    link in a rule only warns: rules are rendered into each harness's own instructions file, where
    it won't resolve."""
    errors, warnings = [], []
    items = [md for s in skills(src) for md in _markdown_under(s)]
    items += markdown_files("agents", src) + markdown_files("commands", src)
    for f in items:  # their links and tags apply checks already
        errors += _check_references(src, f, agent_names, skill_names, links=False, tags=False, prose=True)
    for f in markdown_files("rules", src):
        errors += _check_references(src, f, agent_names, skill_names, links=False, prose=True)
        warnings += [f"{src.rel(f)}: relative link `{t}` won't resolve once the rule is rendered; link a URL"
                     for t in MD_LINK.findall(FENCE.sub("", f.read_text()))
                     if not (re.match(r"^[a-z]+:", t) or t.startswith("#") or "<" in t)]
    for f in [] if src.is_core else _docs(src):
        errors += _check_references(src, f, agent_names, skill_names, prose=True)
    return errors, warnings


# Harness built-in names a core skill must not take.
RESERVED_SKILL_NAMES = frozenset({"review", "plan", "init", "help", "status", "compact"})


def _validate_source(src: Source, agent_names: set[str], skill_names: set[str], plugins=(),
                     local_tripwires: Path | None = None) -> list[str]:
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

    if src.is_core or src.default:
        errors += [f"{src.rel(s)}: skill name `{s.name}` is reserved (a harness built-in); use a `brainrc-` name"
                   for s in skills(src) if s.name in RESERVED_SKILL_NAMES]
    if src.is_core:
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
    harnesses = load_harnesses(include_disabled=True)
    for fragment in sorted(overrides.glob("*/settings.fragment.json")):
        try:
            json.loads(fragment.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{src.rel(fragment)}: invalid JSON ({e})")
        harness = harnesses.get(fragment.parent.name, {})
        if HOOKS_DIR_PLACEHOLDER in fragment.read_text() and "hooks_dir" not in harness:
            errors.append(f"{src.rel(fragment)}: uses {HOOKS_DIR_PLACEHOLDER} but harnesses.toml "
                          f"[{fragment.parent.name}] has no hooks_dir")

    if not src.is_core:
        errors += [f"{src.rel(p)}: no harness in harnesses.toml loads a plugin from overrides/{p.parent.name}/ "
                   "(only one with `plugin` set does)" for p in sorted(overrides.glob("*/plugin.js"))
                   if "plugin" not in harnesses.get(p.parent.name, {})]
        errors += _validate_pack(src)
        errors += extension_errors(src, list(plugins), skill_names, agent_names)
    errors += _check_tripwires(src)
    if src.is_core:
        errors += _check_local_tripwires(src, local_tripwires)
    return errors


def pack_toml_findings(src: Source) -> tuple[list[str], list[str]]:
    """(errors, warnings) for a pack's pack.toml against docs/schemas/pack.toml.schema.json: a known
    key with a value of the wrong type fails; a key the schema doesn't know warns, naming the known
    key it is closest to (a typo such as `max_always_token` would otherwise be silently ignored).
    Only validate reports these: apply installs a pack whatever they say, as it did before."""
    path = src.root / "pack.toml"
    where = src.rel(path)
    if not path.is_file():
        return [], []
    text = path.read_text()
    known = schema.load("pack.toml")
    unknown: list[tuple[tuple, str]] = []
    errors = [f"{where}: {e}" for e in schema.errors(src.meta, known, unknown=unknown)
              if not e.startswith("id:")]  # check_pack_names reports any bad `id`, apply too
    errors += pack_scope.check(src.meta.get("scope"), where)
    errors += guard.check(src.meta, where)
    warnings = []
    for table, key in unknown:
        hint = did_you_mean(key, _known_keys(known, table))
        path_ = tuple(map(str, (*table, key)))
        if "scope" in map(str, table):  # ignored, it would widen the scope to everywhere: fail
            errors.append(f"{where}:{key_line(text, path_)}: unknown key `{'.'.join(path_)}`{hint}; "
                          "a scope key brainrc doesn't know would make the pack apply everywhere")
            continue
        warnings.append(f"{where}:{key_line(text, path_)}: unknown key `{'.'.join(path_)}`{hint}; "
                        "brainrc ignores it")
    return errors, warnings


def _known_keys(known: dict, table: tuple) -> dict:
    """The keys the schema knows in the pack.toml table at `table` (`scope`, a guard rule), for a
    typo's hint; {} for a freer table, such as [extensions]."""
    defs = known.get("$defs", {})
    path = tuple(map(str, table))
    if not path:
        return known["properties"]
    if path[-1] == "scope":
        return defs.get("scope", {}).get("properties", {})
    if path[0] == "guard":
        return defs.get("guard" if len(path) == 1 else "guard_rule", {}).get("properties", {}) if len(path) in (1, 3) else {}
    return {}


def _validate_pack(src: Source) -> list[str]:
    errors = check_pack_names(src)
    for kind in KINDS:
        for p in items(src, kind):
            if not item_name(p).startswith(src.prefix) and not unprefixed_ok(src, item_name(p)):
                errors.append(f"{src.rel(p)}: pack {kind} must start with `{src.prefix}`")
    return errors


def _tripwire_files(src: Source, patterns: list[str]) -> list[Path]:
    found = []
    for dirpath, dirs, files in os.walk(src.root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("dist", "node_modules")]
        for f in files:
            p = Path(dirpath) / f
            rel = p.relative_to(src.root).as_posix()
            if any(fnmatch.fnmatch(rel, pat) for pat in patterns):
                found.append(p)
    return sorted(found)


def _check_tripwires(src: Source) -> list[str]:
    """Stale facts that must not come back: tripwires.toml [[tripwire]] pattern/message/allow/paths."""
    errors = []
    pack_toml = src.root / "pack.toml"
    instructions = connectors.instruction_texts(src) if not src.is_core and pack_toml.is_file() else []
    for t in _read_toml(src.root / "tripwires.toml").get("tripwire", []):
        tid = t.get("id", "?")
        try:
            pattern = re.compile(t["pattern"])
            allow = re.compile(t["allow"]) if t.get("allow") else None
        except (KeyError, re.error) as e:
            errors.append(f"{src.name}:tripwires.toml: tripwire {tid} is invalid ({e})")
            continue
        exclude = t.get("exclude", ["tripwires.toml"])
        scanned = False
        for p in _tripwire_files(src, t.get("paths", ["*.md"])):
            rel = p.relative_to(src.root).as_posix()
            if any(fnmatch.fnmatch(rel, pat) for pat in exclude):
                continue
            scanned = scanned or p == pack_toml
            for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if pattern.search(line) and not (allow and allow.search(line)):
                    errors.append(f"{src.rel(p)}:{n}: tripwire {tid}: {t.get('message', t['pattern'])}")
        # What a pack tells a connector reaches the model too (#136): checked unless the tripwire
        # scanned pack.toml already, names other paths, or excludes it.
        if scanned or "paths" in t or any(fnmatch.fnmatch("pack.toml", pat) for pat in exclude):
            continue
        for name, text in instructions:
            hits = [line for line in text.splitlines() if pattern.search(line) and not (allow and allow.search(line))]
            if hits:
                errors.append(f"{src.rel(pack_toml)}:{_text_line(pack_toml, name, hits[0])}: "
                              f"[{name}] instructions: tripwire {tid}: {t.get('message', t['pattern'])}")
    return errors


def _text_line(pack_toml: Path, table: str, text: str) -> int:
    """The line of pack.toml holding `text` (a line of a table's `instructions`), at or after the
    line that sets it."""
    lines = pack_toml.read_text().splitlines()
    start = line_of("\n".join(lines), table, "instructions")
    return next((n for n, line in enumerate(lines[start - 1:], start) if text.strip() in line), start)


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


def _redacting() -> bool:
    """CI logs can be public: there, local tripwire errors give each term's number, never the term."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def _redact(text: str, needles: list[tuple[str, str]]) -> str:
    """text with every term replaced by `***`; the whole text when case folding hides a match."""
    for t, _ in needles:
        text = re.sub(re.escape(t.strip()), "***", text, flags=re.I)
    return "<path withheld>" if any(n in text.casefold() for _, n in needles) else text


def _check_local_tripwires(src: Source, path: Path | None = None) -> list[str]:
    """Each maintainer's own forbidden terms (an employer, a client), kept out of git in
    tripwires.local.toml as `terms = [...]`: any tracked core file that contains one fails, by name or
    content, compared case-insensitively. The file itself must never be tracked. `path` (from
    `validate --local-tripwires`, which CI writes from a secret) replaces the file at the core root,
    and then must exist and list a term: a check CI was told to run never passes by being skipped."""
    explicit = path is not None
    path = path if explicit else src.root / LOCAL_TRIPWIRES
    label = path.name
    if not path.is_file():
        return [f"{tilde(path)}: not found (--local-tripwires)"] if explicit else []
    files, from_git = _tracked_files(src)
    errors = [f"{label}: is tracked by git; remove it with `git rm --cached {label}`"
              for p in files if from_git and p == path]
    try:
        terms = _read_toml(path).get("terms", [])
    except ConfigError as e:
        return errors + [str(e)]
    if not isinstance(terms, list) or not all(isinstance(t, str) and t.strip() for t in terms):
        return errors + [f"{label}: `terms` must be a list of non-empty strings"]
    if explicit and not terms:
        return errors + [f"{label}: lists no `terms` (--local-tripwires)"]
    needles = [(t, t.strip().casefold()) for t in terms]
    redact = _redacting()

    def found(i: int, t: str, where: str) -> str:
        return f"local tripwire #{i}{where}" if redact else f"local tripwire: {where or 'contains'} \"{t}\" ({label})"

    for p in files if needles else []:
        if p == path or not (p.is_symlink() or p.is_file()):
            continue
        rel = src.rel(p)
        shown = _redact(rel, needles) if redact else rel
        errors += [f"{shown}: {found(i, t, ' in the file name' if redact else 'the file name contains')}"
                   for i, (t, n) in enumerate(needles, 1) if n in rel.casefold()]
        if p.is_symlink():  # git commits the link's target path, not the file it points at
            target = config.readlink(p).casefold()
            errors += [f"{shown}: {found(i, t, ' in the link target' if redact else 'the link target contains')}"
                       for i, (t, n) in enumerate(needles, 1) if n in target]
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            continue  # binary
        for lineno, line in enumerate(data.decode(errors="replace").splitlines(), 1):
            folded = line.casefold()
            errors += [f"{shown}:{lineno}: {found(i, t, '')}"
                       for i, (t, n) in enumerate(needles, 1) if n in folded]
    return errors




def pack_errors(srcs: list[Source]) -> list[tuple[Source, list[str]]]:
    """(pack, errors) for each pack whose own files fail what validate --pack checks; apply runs
    it before linking."""
    agent_names = {f.stem for s in srcs for f in markdown_files("agents", s)}
    skill_names = {p.name for s in srcs for p in skills(s)}
    plugins = validators(srcs)
    found = [(src, _validate_source(src, agent_names, skill_names, plugins)) for src in srcs
             if not src.is_core]
    return [(src, errors) for src, errors in found if errors]


def cmd_validate(pack: str | None = None, key: str = "", fetch_defaults: bool = False,
                 local_tripwires: str | None = None) -> int:
    """key: the pack's packs.toml table when doctor checks an enabled pack, so its validator runs
    only if the user trusts it and its tests don't run (`validate --pack` from the command line
    runs both). fetch_defaults: check against core's default packs at the refs core pins.
    local_tripwires: a terms file to use instead of tripwires.local.toml at the core root."""
    try:
        config_warnings = check_config()
        if pack:
            root = expand(pack).resolve()
            checked = load_pack(root, key or None)
            if fetch_defaults:  # at the refs core pins, in clones of their own (the action, pre-commit)
                defaults, missing = pinned_defaults(skip=checked.name), []
            else:
                defaults, missing = default_sources(skip=checked.name)
            srcs = [Source("core", config.REPO), *defaults, checked]
            config_warnings += missing
        else:
            srcs = sources()
        plugins = validators(srcs)
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    agent_names = {f.stem for s in srcs for f in markdown_files("agents", s)}
    skill_dirs = {p.name: p for s in srcs for p in skills(s)}
    skill_names = set(skill_dirs)
    # `validate --pack` judges the pack as everyone gets it, so this machine's `exclude` doesn't hide
    # a collision; doctor checking an enabled pack (key set) and plain validate use it, as apply does.
    errors = duplicate_packs(srcs) + collisions(srcs, [] if pack and not key else None)
    for src in srcs:
        try:
            errors += _validate_source(src, agent_names, skill_names, plugins,
                                       expand(local_tripwires).resolve() if local_tripwires else None)
        except ConfigError as e:  # a validator plugin that failed
            errors.append(str(e))
    try:
        errors += plugin_errors(srcs, plugins)
    except ConfigError as e:
        errors.append(str(e))
    errors += check_servers(srcs)
    warnings = config_warnings + extension_warnings(srcs, plugins)
    for src in srcs:  # validate-only, like pack.toml's schema: apply installs a pack whatever these say
        errors += connectors.declaration_errors(src)
        found = coverage_findings(src, agent_names, skill_names)
        errors += found[0]
        warnings += found[1]
        if not src.is_core:
            for found in (pack_toml_findings(src), connectors.check(src, skill_dirs)):
                errors += found[0]
                warnings += found[1]
    try:
        errors += check_changelog(core_version())
        compat_errors, compat_warnings = check_packs(srcs)
        warnings += compat_warnings + (compat_deprecations(checked) if pack and not key else [])
        errors += compat_errors
        if not pack:
            errors += check_plugin()
            errors += check_fragments()
        budget_errors, budget_warnings = check_budgets(srcs)
        errors += budget_errors
        warnings += budget_warnings
    except ConfigError as e:
        errors.append(str(e))
    if pack and not key:  # only `validate --pack` from the command line runs a pack's own tests
        errors += packtests.run(checked)

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
