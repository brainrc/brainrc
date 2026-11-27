"""Planning: the links apply makes, stale links, and settings merges to do."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import config, copies
from .config import (
    HOOKS_DIR_PLACEHOLDER,
    KINDS,
    ConfigError,
    expand,
    hook_command_dir,
    installs,
    hooks_copy_root,
    load_harnesses,
    pack_hooks_dir,
    rendered_agents_dir,
    rendered_instructions,
    tilde,
)
from .sources import Source, installed_items, render_instructions, sources
from . import adapters
from .guard import rules_file as guard_rules_file, sandbox as guard_sandbox


def stale_renders(srcs: list[Source], extensions: str | None, agents: dict[Path, str],
                  guard_rules: str | None = None) -> list[tuple[Path, bool]]:
    """The files apply renders (the instructions file the rules go into, extensions.md, the packs'
    guard-rules.json, OpenCode's agent copies) that are missing or differ from what apply would write
    now, as (path, exists). A rule edited since the last apply shows up here, since its link never
    changes. extensions: render_extensions(srcs), None when no enabled pack renders it; guard_rules:
    guard.render(srcs), None when no enabled pack has a guard rule."""
    targets = [(rendered_instructions(), lambda: render_instructions(srcs))]
    if extensions is not None:
        targets.append((config.home_extensions_file(), lambda: extensions))
    if guard_rules is not None:
        targets.append((guard_rules_file(), lambda: guard_rules))
    targets += [(path, lambda text=text: text) for path, text in agents.items()]
    return [(path, exists) for path, render in targets
            if not (exists := path.is_file()) or path.read_text() != render()]


def obsolete_renders(extensions: str | None, agents: dict[Path, str], guard_rules: str | None = None) -> list[Path]:
    """Rendered files apply deletes: extensions.md once no enabled pack renders it, guard-rules.json
    once no enabled pack has a guard rule, and OpenCode agent copies whose agent is gone."""
    gone = [config.home_extensions_file()] if extensions is None and config.home_extensions_file().is_file() else []
    if guard_rules is None and guard_rules_file().is_file():
        gone.append(guard_rules_file())
    for d in rendered_dirs():
        if d.is_dir():
            gone += sorted(p for p in d.glob("*.md") if p not in agents)
    return gone


def rendered_dirs() -> list[Path]:
    """Where agents rendered in another tool's format go, one directory per format (OpenCode's)."""
    try:
        formats = adapters.formats("agents")  # a package's adapter can add a format (#306)
    except ConfigError:  # a broken entry point: apply stops on it; doctor and uninstall go on
        formats = adapters.AGENT_FORMATS
    return [rendered_agents_dir(fmt) for fmt in formats if fmt != "claude"]


def rendered_agents(srcs: list[Source]) -> dict[Path, str]:
    """A rendered copy of every agent for each agent format an enabled harness uses (#306: the
    format's adapter writes it), e.g. OpenCode's, which rejects Claude Code's frontmatter."""
    renderers = {}
    for name, h in load_harnesses().items():
        if (adapter := adapters.agent_renderer(name, h)) is not None:
            renderers.setdefault(adapters.agents_format(name, h), adapter)
    return {rendered_agents_dir(fmt) / f.name: adapter.render_agent(f)
            for fmt, adapter in renderers.items() for src in srcs for f in installed_items(src, "agents")}

@dataclass
class Link:
    harness: str
    dest: Path
    source: Path
    copy: tuple[Path, Path] | None = None  # (overrides dir, copy root): source is a hooks copy

    def state(self, roots: list[Path] | None = None, repair: list[Path] | None = None) -> str:
        """ok | create | update | conflict | edited, or with `repair` (old source roots, possibly
        empty) repair: a link into one of those roots, or a broken link to this item's old location.
        In copy mode (#177) a recorded copy of the source is ok; edited: a recorded copy changed
        by hand since apply wrote it, which apply leaves alone."""
        copying = copies.copying()
        entry = None if self.dest.is_symlink() else copies.recorded(self.dest)
        if entry is not None and os.path.lexists(self.dest):
            if copies.edited(self.dest, entry):
                return "edited"
            if not copying or not copies.current(self.dest, self.source, entry):
                return "update"
            return "ok" if not self.copy or hooks_copy_current(*self.copy) else "update"
        if self.dest.is_symlink():
            target = link_target(self.dest)
            if os.path.normpath(target) == os.path.normpath(self.source):
                if copying:
                    return "update"  # brainrc's link, made before this machine copied
                return "ok" if not self.copy or hooks_copy_current(*self.copy) else "update"
            if _from_former_home(target, self.source):
                return "update"
            if _inside(target, roots or [config.REPO]):
                return "update"
            if repair is not None and (_inside(target, repair) or moved_item(target, self.source)):
                return "repair"
            return "conflict"
        return "conflict" if self.dest.exists() else "create"


def moved_item(target: Path, source: Path) -> bool:
    """True if target is a broken link's target that names the same item as source: the same kind
    dir and name (`skills/x`), as a link into a moved checkout or an old package path does."""
    return not os.path.lexists(target) and target.parts[-2:] == source.parts[-2:]


def old_root(target: Path, source: Path, roots: list[Path]) -> Path | None:
    """The source root a repaired link's target was under: target minus source's path in its root.
    The deepest root wins, so a pack that sat inside core (packs/gatework, before 0.7.1) maps to its own old root."""
    for root in sorted(roots, key=lambda r: len(r.parts), reverse=True):
        if source.is_relative_to(root):
            depth = len(source.relative_to(root).parts)
            return target.parents[depth - 1] if len(target.parts) > depth else None
    return None


def _from_former_home(target: Path, source: Path) -> bool:
    """True if target is the same path under a former settings home that source is under the
    current one: a link apply made before `brainrc migrate` (other links into the old dir stay)."""
    try:
        rel = os.path.normpath(source.relative_to(config.settings_home()))
    except ValueError:
        return False
    for old in config.former_homes():
        if os.path.normpath(target) == os.path.normpath(old / rel):
            return True
    return False


class FragmentError(ConfigError):
    """A settings fragment that isn't valid JSON."""


def render_fragment(fragment: Path, hooks_dir: str | None) -> dict:
    text = fragment.read_text()
    if hooks_dir:
        # The placeholder sits inside a JSON string, so the path goes in JSON-escaped.
        text = text.replace(HOOKS_DIR_PLACEHOLDER, json.dumps(hook_command_dir(hooks_dir))[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        shown = fragment.relative_to(config.REPO).as_posix() if fragment.is_relative_to(config.REPO) else tilde(fragment)
        raise FragmentError(f"{shown}: invalid JSON ({e})") from None


def invalid_fragments(srcs: list[Source]) -> list[str]:
    """Each source's settings fragments that aren't valid JSON, as `<file>: invalid JSON (...)`."""
    errors = []
    for src in srcs:
        for fragment in sorted((src.root / "overrides").glob("*/settings.fragment.json")):
            try:
                json.loads(fragment.read_text())
            except json.JSONDecodeError as e:
                errors.append(f"{src.rel(fragment)}: invalid JSON ({e})")
    return errors


@dataclass
class SettingsMerge:
    harness: str
    dest: Path
    fragments: list[tuple[Path, str | None]]  # (fragment, hooks dir) per source, in order
    extra_markers: set[str] = field(default_factory=set)
    fmt: str = "claude"  # harnesses.toml settings_format: where the file keeps its hooks
    sandbox: dict = field(default_factory=dict)  # guard.sandbox(): packs' path and host rules (#322)
    # A removal from a tool brainrc doesn't manage (off, never applied): a file it can't parse with
    # nothing of brainrc's in it is left alone, not a conflict (a Gemini CLI settings.json with comments).
    lenient: bool = False

    def wanted(self) -> dict:
        hooks: dict[str, list] = {}
        wanted: dict = {}
        perms: dict = {}
        box: dict = {}
        for fragment, hooks_dir in self.fragments:
            rendered = render_fragment(fragment, hooks_dir)
            for event, groups in rendered.get("hooks", {}).items():
                hooks.setdefault(event, []).extend(groups)
            for key, value in (rendered.get("permissions") or {}).items() \
                    if isinstance(rendered.get("permissions"), dict) else ():
                if key in ("allow", "deny", "ask"):  # every source's entries, in order; only a list counts
                    entries = [e for e in value if isinstance(e, str)] if isinstance(value, list) else []
                    perms[key] = list(dict.fromkeys([*perms.get(key, []), *entries]))
                else:
                    perms.setdefault(key, value)
            if isinstance(rendered.get("sandbox"), dict):
                _join_sandbox(box, rendered["sandbox"])
            for key, value in rendered.items():  # e.g. Cursor's "version"; the first source wins
                if key not in ("hooks", "permissions", "sandbox"):
                    wanted.setdefault(key, value)
        if perms:
            wanted["permissions"] = perms
        _join_sandbox(box, self.sandbox)  # packs' path and host rules after the fragments'
        if box:
            wanted["sandbox"] = box
        wanted["hooks"] = hooks
        return wanted

    def markers(self) -> set[str]:
        dirs = {hd for _, hd in self.fragments if hd} | self.extra_markers
        return {hook_command_dir(d).rstrip("/") + "/" for d in dirs}


def _join_sandbox(box: dict, more: dict) -> None:
    """Add more's sandbox keys into box: each source's list entries in order, any other value from
    the first source that sets it (e.g. enabled)."""
    for key, value in more.items():
        if isinstance(value, dict) and isinstance(box.setdefault(key, {}), dict):
            part = box[key]
            for k, v in value.items():
                if isinstance(v, list):
                    have = part.get(k) if isinstance(part.get(k), list) else []
                    part[k] = list(dict.fromkeys([*have, *(e for e in v if isinstance(e, str))]))
                else:
                    part.setdefault(k, v)
        elif not isinstance(value, dict):
            box.setdefault(key, value)


def link_target(link: Path) -> Path:
    """Where a symlink points, with relative targets resolved against the link's directory."""
    target = Path(config.readlink(link))
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
    return _inside(path, [config.REPO])


def _hook_files(root: Path) -> dict[Path, bytes]:
    """Every file under root/<harness>/hooks/, keyed by its path relative to root."""
    return {p.relative_to(root): p.read_bytes() for p in sorted(root.glob("*/hooks/**/*"))
            if p.is_file() and "__pycache__" not in p.parts}


def hooks_copy_current(overrides: Path, copy_root: Path) -> bool:
    """True if copy_root holds exactly the hooks dirs under overrides."""
    return copy_root.is_dir() and _hook_files(overrides) == _hook_files(copy_root)


def _pack_plugin(target: Path) -> bool:
    """True if target is some pack's overrides/<harness>/plugin.js, whether or not the pack is
    still configured."""
    t = Path(os.path.abspath(target))
    return t.name == "plugin.js" and t.parent.parent.name == "overrides"


def _managed_target(target: Path, roots: list[Path]) -> bool:
    """True if target is a path brainrc itself links to: in a source root, or the hooks copy."""
    t = Path(os.path.abspath(target)).resolve()
    if t == rendered_instructions().resolve() or t.parent in {d.resolve() for d in rendered_dirs()}:
        return True
    for root in (r.resolve() for r in roots):
        if t.parent in {root / k for k in KINDS}:
            return True
        if t == root / "dist" / "instructions.md":  # pre-0.3.16 render location
            return True
        if t.name in ("hooks", "plugin.js") and t.parent.parent == root / "overrides":
            return True
    copy_roots = [hooks_copy_root()] + [old / "hooks" / "core" for old in config.former_homes()]
    return t.name == "hooks" and t.parent.parent in {r.resolve() for r in copy_roots}


def stale_hooks_copy(links: list[Link]) -> Path | None:
    """The hooks copy when no planned link uses it any more (every hooked harness disabled)."""
    root = hooks_copy_root()
    return root if root.exists() and not any(link.copy for link in links) else None


def _scoped(harnesses: dict[str, dict]) -> dict[str, dict]:
    """The harnesses inside `--only` (all of them without it)."""
    return {n: h for n, h in harnesses.items() if config.in_scope(n)}


def plan(srcs: list[Source] | None = None, every_src: list[Source] | None = None,
         old_roots: list[Path] | None = None) -> tuple[list[Link], list[Path], list[SettingsMerge]]:
    """old_roots (apply --repair): where sources used to be, so links into them count as stale."""
    srcs = srcs if srcs is not None else sources()
    every_src = every_src if every_src is not None else sources(include_disabled=True)
    roots = [s.root for s in every_src] + (old_roots or [])
    links: list[Link] = []
    merges: list[SettingsMerge] = []
    hooks_on = installs("hooks")  # the minimal profile installs rules only (#173)
    for name, h in _scoped(load_harnesses()).items():
        for kind in KINDS:
            if kind in h:
                d = expand(h[kind])
                fmt = adapters.agents_format(name, h) if kind == "agents" else "claude"
                links += [Link(name, d / p.name, rendered_agents_dir(fmt) / p.name if fmt != "claude" else p)
                          for src in srcs for p in installed_items(src, kind)]
        if "instructions" in h:
            links.append(Link(name, expand(h["instructions"]), rendered_instructions()))
        if "plugin" in h and hooks_on:  # one file the harness loads as a plugin (OpenCode's guards)
            links.append(Link(name, expand(h["plugin"]), config.REPO / "overrides" / name / "plugin.js"))
            links += [Link(name, expand(config.pack_plugin_path(h["plugin"], src.name)), own)  # a pack's own (#137)
                      for src in srcs if not src.is_core
                      if (own := src.root / "overrides" / name / "plugin.js").is_file()]
        fragments: list[tuple[Path, str | None]] = []
        for src in srcs if hooks_on else []:
            hooks = src.root / "overrides" / name / "hooks"
            hooks_dir = None
            if "hooks_dir" in h:
                hooks_dir = h["hooks_dir"] if src.is_core else pack_hooks_dir(h["hooks_dir"], src.name)
                if src.is_core and config.installed():  # a package path changes with Python
                    links.append(Link(name, expand(hooks_dir), hooks_copy_root() / name / "hooks",
                                      (src.root / "overrides", hooks_copy_root())))
                elif src.is_core or hooks.is_dir():
                    links.append(Link(name, expand(hooks_dir), hooks))
            fragment = src.root / "overrides" / name / "settings.fragment.json"
            if fragment.is_file():
                fragments.append((fragment, hooks_dir))
        box = guard_sandbox(srcs, name) if "settings" in h and hooks_on else {}  # minimal: rules only
        if "settings" in h and (fragments or box):
            known = {pack_hooks_dir(h["hooks_dir"], s.name) for s in every_src if "hooks_dir" in h}
            merges.append(SettingsMerge(name, expand(h["settings"]), fragments, known,
                                        adapters.settings_format(name, h), box))
        elif "settings" in h and "hooks_dir" in h and not hooks_on:  # take brainrc's hooks back out
            known = {h["hooks_dir"]} | {pack_hooks_dir(h["hooks_dir"], s.name) for s in every_src}
            merges.append(SettingsMerge(name, expand(h["settings"]), [], known, adapters.settings_format(name, h)))
    # A disabled harness keeps its settings file, so take brainrc's hooks back out of it:
    # merging no fragments removes only the groups brainrc owns.
    enabled = load_harnesses()
    for name, h in _scoped(load_harnesses(include_disabled=True)).items():
        if name not in enabled and "settings" in h:
            known = set()
            if "hooks_dir" in h:
                known = {h["hooks_dir"]} | {pack_hooks_dir(h["hooks_dir"], s.name) for s in every_src}
            merges.append(SettingsMerge(name, expand(h["settings"]), [], known, adapters.settings_format(name, h),
                                        lenient=True))

    # Stale: links brainrc made earlier that it wouldn't make now (removed items, disabled packs,
    # disabled harnesses). Only symlinks pointing at a path brainrc links to are touched.
    wanted = {link.dest for link in links}
    candidates: set[Path] = set()
    orphans: set[Path] = set()
    for h in _scoped(load_harnesses(include_disabled=True)).values():
        for kind in KINDS:
            d = expand(h[kind]) if kind in h else None
            if d and d.is_dir():
                candidates.update(d.iterdir())
        if "instructions" in h:
            candidates.add(expand(h["instructions"]))
        if "plugin" in h:
            candidates.add(expand(h["plugin"]))
            candidates.update(expand(old) for old in config.former_plugin_paths(h["plugin"]))
            candidates.update(expand(config.pack_plugin_path(h["plugin"], s.name)) for s in every_src)
            # A pack's plugin runs on every tool call, so its link goes with the pack even when the
            # pack's entry was deleted from packs.toml (every_src no longer names it).
            mine = expand(config.pack_plugin_path(h["plugin"], "*"))
            orphans.update(q for q in (mine.parent.glob(mine.name) if mine.parent.is_dir() else [])
                           if q.is_symlink() and _pack_plugin(link_target(q)))
        if "hooks_dir" in h:
            candidates.add(expand(h["hooks_dir"]))
            candidates.update(expand(pack_hooks_dir(h["hooks_dir"], s.name)) for s in every_src)
            for old in config.former_hooks_dirs(h["hooks_dir"]):  # the pre-rename names
                candidates.add(expand(old))
                candidates.update(expand(pack_hooks_dir(old, s.name)) for s in every_src)
    stale = sorted(p for p in candidates | orphans
                   if p.is_symlink() and p not in wanted and (p in orphans or _managed_target(link_target(p), roots)))
    stale += copies.stale(wanted, config.in_scope)[0]  # copies apply made and no longer makes (#177)
    return links, stale, merges


def edited_stale_copies(links: list[Link]) -> list[Path]:
    """Copies apply made, no longer makes, and that were edited since: left alone and reported."""
    return copies.stale({link.dest for link in links}, config.in_scope)[1]
