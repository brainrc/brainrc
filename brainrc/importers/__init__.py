"""`brainrc import`: turn instruction files other tools read into a pack (E12, #118).

Each format has a module with `detect(path)` and `read(path) -> Imported`. `plan` runs the
importers in the order the sources were given and joins what they return into one PackSpec;
`brainrc.scaffold` writes it. Rules keep their order and a provenance comment.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .. import config
from ..config import ConfigError, config_path, expand, table_span, tilde, write_text_atomic
from ..scaffold import PackSpec, render_pack, write_pack
from . import copilot, cursor, instructions, plugin, windsurf

# Format name -> importer module, in the order discover() lists what it finds.
FORMATS = {"instructions": instructions, "cursor": cursor, "copilot": copilot, "windsurf": windsurf,
           "plugin": plugin}
DEFAULT_NAME = "imported"
HOOKS_FRAGMENT = "overrides/claude/settings.fragment.json"


def detect(path: Path) -> str | None:
    """The format of one source file or folder, or None."""
    return next((name for name, mod in FORMATS.items() if mod.detect(path)), None)


def discover(root: Path) -> list[tuple[str, Path]]:
    """(format, path) for each source this folder holds that an importer reads, in FORMATS order:
    what `brainrc import <dir>` and `brainrc init` offer."""
    found = []
    for fmt, mod in FORMATS.items():
        for rel in getattr(mod, "LOOK_FOR", getattr(mod, "NAMES", ())):
            path = root / rel
            if (path.is_file() or path.is_dir()) and mod.detect(path):
                found.append((fmt, path))
    return found


@dataclass
class Plan:
    spec: PackSpec
    files: dict[str, str]
    sources: list[tuple[str, Path]]
    warnings: list[str] = field(default_factory=list)


def plan(sources: list[tuple[str, Path]], name: str = DEFAULT_NAME, prefix: str = "") -> Plan:
    """The pack the sources become, rendered but not written."""
    spec = PackSpec(name, prefix)
    warnings: list[str] = []
    got = [FORMATS[fmt].read(path) for fmt, path in sources]
    used, taken, kept_reads = [], set(), set()
    hooks: dict[str, list] = {}
    for i, ((fmt, path), one) in enumerate(zip(sources, got)):
        me = path.resolve()
        # A file another source inlines (CLAUDE.md's `@AGENTS.md`) comes in there, whatever the order.
        by = [p for j, (_, p) in enumerate(sources) if j != i and me in got[j].read and p.resolve() not in one.read]
        if me in kept_reads or by:
            warnings.append(f"{tilde(path)}: already imported with "
                            f"{tilde(by[0]) if by else 'a source above'}; skipped")
            continue
        kept_reads |= one.read
        used.append((fmt, path))
        renamed = {}
        for kind, found in (("skills", one.skills), ("agents", one.agents), ("commands", one.commands)):
            for item in found:  # two sources with an item of the same name: number the later one
                base = item.slug.removeprefix(spec.prefix) or item.slug  # `acme-x` is `x` in acme
                slug, n = base, 2
                while (kind, slug) in taken:
                    slug, n = f"{base}-{n}", n + 1
                renamed[(kind, item.slug)], item.slug = slug, slug
                taken.add((kind, slug))
        names = {kind: {old: f"{spec.prefix}{renamed[(kind, slug)]}" for old, slug in olds.items()}
                 for kind, olds in one.renames.items()}
        server_slugs = {}
        for name, table in one.servers.items():
            base = name.removeprefix(spec.prefix) or name
            slug, n = base, 2
            while slug in spec.servers:
                slug, n = f"{base}-{n}", n + 1
            spec.servers[slug] = table
            server_slugs[name] = slug
        servers = {old: f"{spec.prefix}{server_slugs[slug]}" for old, slug in one.server_names.items()}
        for item in (*one.skills, *one.agents, *one.commands):
            item.text = _rewrite_tools(_rewrite(item.text, names, one.namespace), servers, one.namespace)
        for agent in one.agents:
            agent.tools = _rewrite_tools(agent.tools, servers, one.namespace)
        spec.rules += one.rules
        spec.skills += one.skills
        spec.agents += one.agents
        spec.commands += one.commands
        spec.domains += [{**row, "skills": [f"{spec.prefix}{renamed.get(('skills', s), s)}" for s in row["skills"]]}
                         for row in one.domains]
        for event, groups in one.hooks.items():
            hooks.setdefault(event, []).extend(json.loads(_rewrite_tools(json.dumps(groups), servers, one.namespace)))
        for rel, data in one.pack_files.items():
            if rel in spec.files:
                raise ConfigError(f"two sources both write {rel}; import them one at a time")
            spec.files[rel] = data
        warnings += one.warnings
    if hooks:
        spec.files[HOOKS_FRAGMENT] = json.dumps({"hooks": hooks}, indent=2) + "\n"
    spec.description = "Imported by brainrc import from " + ", ".join(
        f"{p.parent.name}/{p.name}" if p.is_dir() else p.name for _, p in used)
    return Plan(spec, render_pack(spec), used, warnings)


def _rewrite(text: str, names: dict[str, dict[str, str]], namespace: str) -> str:
    """text with a source's own names for its skills and agents changed to the pack's: in
    `[agent: x]` tags, "`x` skill", and a plugin's `namespace:x` (Claude Code's `/plugin:skill`)."""
    for old, new in names.get("agents", {}).items():
        text = re.sub(rf"\[agent:\s*{re.escape(old)}\]", f"[agent: {new}]", text)
    for old, new in names.get("skills", {}).items():
        text = text.replace(f"`{old}` skill", f"`{new}` skill")
    every = {old: new for olds in names.values() for old, new in olds.items()}
    if namespace and every:
        alts = "|".join(map(re.escape, sorted(every, key=len, reverse=True)))
        text = re.sub(rf"(?<![\w-]){re.escape(namespace)}:({alts})(?![\w-])", lambda m: every[m[1]], text)
    return text


def _rewrite_tools(text: str, servers: dict[str, str], namespace: str) -> str:
    """text with a source's MCP tool names (`mcp__<server>__x`, and a plugin's own
    `mcp__plugin_<plugin>_<server>__x`) changed to the server's name in the pack."""
    for old, new in sorted(servers.items(), key=lambda kv: len(kv[0]), reverse=True):
        olds = [f"mcp__plugin_{namespace}_{old}__"] if namespace else []
        for o in [*olds, f"mcp__{old}__"]:
            text = re.sub(rf"(?<![\w-]){re.escape(o)}", f"mcp__{new}__", text)
    return text


def resolve(paths: list[str], fmt: str | None = None) -> list[tuple[str, Path]]:
    """(format, path) for each path named on the command line; a folder means what it holds."""
    out: list[tuple[str, Path]] = []
    for raw in paths:
        path = expand(raw).resolve()
        if not path.exists():
            raise ConfigError(f"{raw}: no such file or folder")
        if fmt:
            if path.is_dir() and not FORMATS[fmt].detect(path):
                inside = [(f, p) for f, p in discover(path) if f == fmt]
                if not inside:
                    raise ConfigError(f"{raw}: a folder with no {fmt} sources in it; name the files")
                out += inside
            else:
                out.append((fmt, path))
        elif found := detect(path):
            out.append((found, path))
        elif path.is_dir() and (inside := discover(path)):
            out += inside
        else:
            known = ", ".join(n for m in FORMATS.values() for n in getattr(m, "NAMES", ()))
            raise ConfigError(f"{raw}: not a format brainrc imports ({known}); name one with --format")
    return list(dict.fromkeys(out))


def summary(spec: PackSpec, files: dict[str, str]) -> str:
    from ..tokens import estimate_tokens
    always = sum(estimate_tokens(t) for rel, t in files.items() if rel.startswith("rules/"))
    always += sum(estimate_tokens(s.description) for s in spec.skills)
    always += sum(estimate_tokens(i.description) for i in (*spec.agents, *spec.commands))
    parts = [f"{len(spec.rules)} rules", f"{len(spec.skills)} skills"]
    parts += [f"{len(found)} {kind}" for kind, found in (("agents", spec.agents), ("commands", spec.commands),
                                                         ("MCP servers", spec.servers)) if found]
    if HOOKS_FRAGMENT in spec.files:
        parts.append("hooks")
    return f"{len(files)} files: {', '.join(parts)}, ~{always} always-loaded tokens"


def set_pack_path(text: str, name: str, path: str) -> str:
    """text (a packs.local.toml) with [name] path = path and on: a new table, or that table's
    `path`, `git`, `ref` and `enabled` replaced by the path."""
    line = f'path = "{path}"\n'
    lines = text.splitlines(keepends=True)
    span = table_span(lines, name)
    if span is None:
        head = text.rstrip("\n") + "\n\n" if text.strip() else ""
        return f"{head}[{name}]\n{line}"
    start, end = span
    for i in range(start + 1, end):
        if re.match(r"\s*[\"']?(path|git|ref|enabled)[\"']?\s*=", lines[i]):
            lines[i] = ""
    if not lines[start].endswith("\n"):
        lines[start] += "\n"
    lines.insert(start + 1, line)
    return "".join(lines)


def default_dest(name: str) -> Path:
    return config.settings_home() / "imported" / name


def enable(name: str, dest: Path, dry_run: bool = False) -> str:
    """Add the pack to packs.local.toml; the message to print."""
    packs_file = config.local_dir() / "packs.local.toml"
    before = packs_file.read_text() if packs_file.is_file() else ""
    try:
        tomllib.loads(before)
    except tomllib.TOMLDecodeError as e:
        raise config.toml_error(packs_file, before, e) from None
    after = set_pack_path(before, name, config_path(dest))
    tomllib.loads(after)  # the setter keeps it valid; fail loudly rather than write a file apply can't read
    if after != before and not dry_run:
        write_text_atomic(packs_file, after)
    return f"{'Would add' if dry_run else 'Added'} [{name}] to {tilde(packs_file)}."


def why(e: OSError | UnicodeDecodeError) -> str:
    if isinstance(e, UnicodeDecodeError):
        return f"a source isn't UTF-8 text ({e.reason} at byte {e.start}); save it as UTF-8 and import again"
    return f"{tilde(Path(e.filename)) + ': ' if e.filename else ''}{e.strerror or e}"


def cmd_import(paths: list[str], to: str | None = None, name: str = DEFAULT_NAME, prefix: str = "",
               fmt: str | None = None, force: bool = False, dry_run: bool = False,
               enable_pack: bool = False) -> int:
    try:
        sources = resolve(paths, fmt)
        p = plan(sources, name, prefix)
        if not (p.spec.rules or p.spec.skills or p.spec.agents or p.spec.commands or p.spec.servers
                or p.spec.files):
            raise ConfigError("nothing to import: " + "; ".join(p.warnings or ["the sources are empty"]))
        dest = expand(to) if to else default_dest(name)
        dest = dest if dest.is_absolute() else Path.cwd() / dest
        for w in p.warnings:
            print(f"WARN {w}")
        for fmt_name, path in p.sources:
            print(f"Import {tilde(path)} ({fmt_name})")
        if dry_run:
            for rel in p.files:
                print(f"  would write {rel}")
            print(f"Would write {tilde(dest)}: {summary(p.spec, p.files)}.")
            if enable_pack:
                print(enable(name, dest, dry_run=True))
            return 0
        write_pack(dest, p.files, force=force, sources=[path for _, path in p.sources])
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(f"ERROR {why(e)}")
        return 1
    print(f"Wrote {tilde(dest)}: {summary(p.spec, p.files)}.")
    from ..validate import cmd_validate
    code = cmd_validate(pack=str(dest))
    if code:
        return code
    return next_steps(name, dest, enable_pack, " (or import again with --enable)")


def next_steps(name: str, dest: Path, enable_pack: bool, again: str = "") -> int:
    """After a new pack is written and validates: add it to packs.local.toml, or say how to load it,
    on this machine or (when it's inside the current folder) for this project in brainrc.toml."""
    if enable_pack:
        try:
            print(enable(name, dest))
        except (ConfigError, OSError) as e:
            print(f"ERROR {e}")
            return 1
        print(f"Next: `{config.command('status')}` to see the changes, then `{config.command('apply')}`.")
        return 0
    print(f"To load it on this machine, add it to packs.local.toml{again}:\n\n"
          f"[{name}]\npath = \"{config_path(dest)}\"")
    if dest.is_relative_to(Path.cwd()):
        print(f"\nOr, for this project only, to brainrc.toml:\n\n[packs.{name}]\n"
              f"path = \"{dest.relative_to(Path.cwd()).as_posix()}\"")
    return 0
