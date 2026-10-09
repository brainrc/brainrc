"""aicfg: sync this repo's skills, agents, commands, rules, and hooks into AI harnesses.

Usage:
  aicfg.py status                show what would change (default, no writes)
  aicfg.py apply                 render rules and pack extensions to $AICFG_HOME (default
                                 ~/.config/ai-config), create/refresh symlinks, merge settings
  aicfg.py validate [--pack DIR] check frontmatter, cross-references, packs, and tripwires
                                 (used in CI); --pack checks core plus that pack only
  aicfg.py doctor                diagnose this machine's install (read-only): stale renders,
                                 missing/broken links, broken packs, unmerged hooks; exits 1
                                 on any problem, each with its fix
  aicfg.py plugin                write the plugin manifests (.claude-plugin/, plugin.json);
                                 validate fails when they're stale
  aicfg.py tokens                estimate the context cost of every skill, agent, and command

Sources: this repo ("core", versioned by VERSION) plus any packs listed in packs.toml /
packs.local.toml. A pack is a repo with the same layout and a pack.toml (see docs/packs.md);
its `requires_core` must match VERSION, or validate fails and apply writes nothing.

Safety: never overwrites a real file or a symlink pointing outside this repo or a pack.
Those are reported as CONFLICT and left alone for you to resolve. Settings files
are merged (only entries owned by ai-config are replaced) and backed up first.
"""
from __future__ import annotations

from .config import (
    ConfigError,
    extensions_file,
    home_extensions_file,
    legacy_instructions,
    rendered_agents_dir,
    rendered_instructions,
    tilde,
)
from .sources import check_packs, collisions, render_extensions, render_instructions, sources
from .opencode import rendered_agents
from .plan import plan
from .settings import settings_change, write_settings
from .plugin import cmd_plugin
from .tokens import cmd_tokens
from .validate import cmd_validate
from .doctor import cmd_doctor


def cmd_sync(apply: bool) -> int:
    try:
        srcs = sources()
        roots = [s.root for s in sources(include_disabled=True)]
        agents = rendered_agents(srcs)
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
        for path, text in agents.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        if rendered_agents_dir().is_dir():
            for old in rendered_agents_dir().glob("*.md"):
                if old not in agents:
                    old.unlink()
        if legacy_instructions().is_file():
            legacy_instructions().unlink()
            if not any(legacy_instructions().parent.iterdir()):
                legacy_instructions().parent.rmdir()

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
