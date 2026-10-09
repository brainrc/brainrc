"""Planning: the links apply makes, stale links, and settings merges to do."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .config import (
    HOOKS_DIR_PLACEHOLDER,
    KINDS,
    expand,
    hook_command_dir,
    load_harnesses,
    pack_hooks_dir,
    rendered_agents_dir,
    rendered_instructions,
)
from .sources import Source, items, sources
from .opencode import agents_format


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
            return "update" if _inside(target, roots or [config.REPO]) else "conflict"
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
    return _inside(path, [config.REPO])


def _managed_target(target: Path, roots: list[Path]) -> bool:
    """True if target is a path aicfg itself links to inside one of the source roots."""
    t = Path(os.path.abspath(target)).resolve()
    if t == rendered_instructions().resolve() or t.parent == rendered_agents_dir().resolve():
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
                rendered = kind == "agents" and agents_format(h) == "opencode"
                links += [Link(name, d / p.name, rendered_agents_dir() / p.name if rendered else p)
                          for src in srcs for p in items(src, kind)]
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
