"""aicfg: sync this repo's skills, agents, commands, rules, and hooks into AI harnesses.

Usage:
  aicfg.py status                show what would change (default, no writes)
  aicfg.py apply                 render rules and pack extensions to $AICFG_HOME (default
                                 ~/.config/ai-config), create/refresh symlinks, merge settings
                                 and MCP servers (mcp/servers.toml)
  aicfg.py validate [--pack DIR] check frontmatter, cross-references, packs, and tripwires
                                 (used in CI); --pack checks core plus that pack only
  aicfg.py doctor                diagnose this machine's install (read-only): stale renders,
                                 missing/broken links, broken packs, unmerged hooks; exits 1
                                 on any problem, each with its fix
  aicfg.py plugin                write the plugin manifests (.claude-plugin/, plugin.json);
                                 validate fails when they're stale
  aicfg.py release [--dry-run]   fold changelog.d/ fragments into CHANGELOG.md, bump VERSION,
                                 and rewrite the plugin manifests (the release workflow runs it)
  aicfg.py tokens                estimate the context cost of every skill, agent, and command
  aicfg.py update                refetch packs named by `git` URL at their `ref`, then apply

Sources: this repo ("core", versioned by VERSION) plus any packs listed in packs.toml /
packs.local.toml, by `path` or by `git` URL (fetched into $AICFG_HOME/packs). A pack is a
repo with the same layout and a pack.toml (see docs/packs.md);
its `requires_core` must match VERSION, or validate fails and apply writes nothing.

Safety: never overwrites a real file or a symlink pointing outside this repo or a pack.
Those are reported as CONFLICT and left alone for you to resolve. Settings files
are merged (only entries owned by ai-config are replaced) and backed up first.
"""
from __future__ import annotations

import sys

from . import config
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
from .packs import describe, fetch_pack, git_packs
from .plan import invalid_fragments, plan
from .mcp import check_servers, mcp_change, mcp_plan, record_owned, write_mcp
from .settings import settings_change, write_settings
from .plugin import cmd_plugin
from .release import cmd_release
from .tokens import cmd_tokens
from .validate import cmd_validate
from .doctor import cmd_doctor


def cmd_sync(apply: bool) -> int:
    try:
        pending = [(key, cfg, root) for key, cfg, root in git_packs() if not root.exists()]
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    for key, cfg, root in pending:
        print(describe(key, cfg))
        if apply:
            try:
                fetch_pack(key, cfg, root)
            except ConfigError as e:
                print(f"ERROR {e}")
                print("\nNothing written. Check the pack's `git` and `ref`, then re-run.")
                return 1
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
    bad_fragments = invalid_fragments(srcs)
    if bad_fragments:
        for e in bad_fragments:
            print(f"ERROR {e}")
        print("\nNothing written. Fix the JSON, then re-run.")
        return 1
    bad_servers = check_servers(srcs)
    if bad_servers:
        for e in bad_servers:
            print(f"ERROR {e}")
        print("\nNothing written. Fix mcp/servers.toml, then re-run.")
        return 1

    if apply:
        rendered = rendered_instructions()
        rendered.parent.mkdir(parents=True, exist_ok=True)
        rendered.write_text(render_instructions(srcs))
        extensions = render_extensions(srcs)
        home_extensions_file().write_text(extensions)
        if extensions_file().parent.is_dir() and not config.installed():
            extensions_file().write_text(extensions)
        for path, text in agents.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        if rendered_agents_dir().is_dir():
            for old in rendered_agents_dir().glob("*.md"):
                if old not in agents:
                    old.unlink()
        if not config.installed() and legacy_instructions().is_file():
            legacy_instructions().unlink()
            if not any(legacy_instructions().parent.iterdir()):
                legacy_instructions().parent.rmdir()

    links, stale, merges = plan(srcs)
    conflicts, changes = 0, len(pending)
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
    for s in mcp_plan(srcs):
        state, text, clashing, owned = mcp_change(s)
        for name in clashing:
            conflicts += 1
            print(f"{'CONFLICT':9} {s.harness:9} {tilde(s.dest)}  (your own MCP server `{name}`; "
                  "rename it or remove it to let ai-config manage it)")
        if state == "invalid":
            conflicts += 1
            print(f"{'CONFLICT':9} {s.harness:9} {tilde(s.dest)}  (can't parse it, fix by hand)")
        elif state == "merge":
            changes += 1
            print(f"{'MERGE':9} {s.harness:9} {tilde(s.dest)}  (mcp)")
            if apply:
                write_mcp(s, text, owned)
        elif apply:
            record_owned(s, owned)  # e.g. adopt entries that already match after lost state

    if not changes and not conflicts:
        print("Everything in sync.")
    elif not apply and changes:
        print("\nDry run. Run `apply` to write.")
    if conflicts:
        print(f"\n{conflicts} conflict(s): existing files not managed by this repo. "
              "Move them into the repo (or delete them), then re-run.")
    return 1 if conflicts else 0


def cmd_update() -> int:
    """Refetch every git pack at its `ref`, then apply."""
    try:
        for key, cfg, root in git_packs():
            print(describe(key, cfg))
            fetch_pack(key, cfg, root)
    except ConfigError as e:
        print(f"ERROR {e}")
        print("\nNothing applied. Fix it, then re-run update.")
        return 1
    return cmd_sync(apply=True)


def entry() -> None:
    """The `aicfg` console script of an installed package."""
    sys.exit(main(sys.argv))


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
    if cmd == "release" and (len(argv) == 2 or argv[2:] == ["--dry-run"]):
        return cmd_release(dry_run=len(argv) == 3)
    if cmd == "doctor" and len(argv) == 2:
        return cmd_doctor()
    if cmd == "update" and len(argv) == 2:
        return cmd_update()
    if cmd == "tokens" and len(argv) == 2:
        return cmd_tokens()
    print(__doc__.replace("aicfg.py ", "aicfg ") if config.installed() else __doc__)
    return 2
