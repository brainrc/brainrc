"""brainrc: sync this repo's skills, agents, commands, rules, and hooks into AI harnesses.

Usage:
  brainrc.py status                show what would change (default, no writes)
  brainrc.py apply                 render rules and pack extensions to $AICFG_HOME (default
                                   ~/.config/ai-config), create/refresh symlinks, merge settings
                                   and MCP servers (mcp/servers.toml)
  brainrc.py validate [--pack DIR] check frontmatter, cross-references, packs, and tripwires
                                   (used in CI); --pack checks core plus that pack only
  brainrc.py doctor                diagnose this machine's install (read-only): stale renders,
                                   missing/broken links, broken packs, unmerged hooks; exits 1
                                   on any problem, each with its fix
  brainrc.py plugin                write the plugin manifests (.claude-plugin/, plugin.json);
                                   validate fails when they're stale
  brainrc.py release [--dry-run]   fold changelog.d/ fragments into CHANGELOG.md, bump VERSION,
                                   and rewrite the plugin manifests (the release workflow runs it)
  brainrc.py release --notes X.Y.Z print that version's CHANGELOG.md section (GitHub Release body)
  brainrc.py tokens                estimate the context cost of every skill, agent, and command
  brainrc.py update                refetch packs named by `git` URL at their `ref`, then apply
  brainrc.py --version             print `brainrc <VERSION>`

Sources: this repo ("core", versioned by VERSION) plus any packs listed in packs.toml /
packs.local.toml, by `path` or by `git` URL (fetched into $AICFG_HOME/packs). A pack is a
repo with the same layout and a pack.toml (see docs/packs.md);
its `requires_core` must match VERSION, or validate fails and apply writes nothing.

Safety: never overwrites a real file or a symlink pointing outside this repo or a pack.
Those are reported as CONFLICT and left alone for you to resolve. Settings files
are merged (only entries owned by ai-config are replaced) and backed up first.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from . import config
from .config import (
    ConfigError,
    aicfg_home,
    check_config,
    extensions_file,
    home_extensions_file,
    legacy_instructions,
    rendered_agents_dir,
    rendered_instructions,
    tilde,
)
from .sources import (
    check_packs, collisions, core_version, duplicate_packs, render_extensions, render_instructions, sources,
)
from .opencode import rendered_agents
from .packs import describe, fetch_pack, git_packs, needs_fetch
from .plan import hooks_copy_current, invalid_fragments, plan, stale_hooks_copy
from .mcp import check_servers, mcp_change, mcp_plan, record_owned, write_mcp
from .settings import FileChanged, read_current, settings_change, write_settings
from .plugin import cmd_plugin
from .release import cmd_release, cmd_release_notes
from .tokens import cmd_tokens
from .validate import cmd_validate, pack_errors
from .doctor import cmd_doctor


CHANGED_HINT = "(changed during apply; close Claude Code and re-run)"


def cmd_sync(apply: bool) -> int:
    """status (apply=False) or apply; apply holds $AICFG_HOME/apply.lock while it runs."""
    if not apply:
        return _sync(False)
    lock = aicfg_home() / "apply.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "a") as f:
        if not _try_lock(f):
            print(f"ERROR another brainrc apply is running (lock: {tilde(lock)})")
            print("\nNothing written. Let it finish, then re-run.")
            return 1
        return _sync(True)


def _try_lock(f) -> bool:
    """Exclusive and non-blocking. The OS releases it when the file closes or the process dies."""
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _copy_hooks(overrides: Path, copy_root: Path) -> None:
    """Replace copy_root with every overrides/<harness>/hooks dir: build beside it, then swap."""
    if hooks_copy_current(overrides, copy_root):
        return
    tmp = copy_root.with_name(f".{copy_root.name}.aicfg-tmp-{os.getpid()}")
    old = copy_root.with_name(f".{copy_root.name}.aicfg-old-{os.getpid()}")
    for stale in (tmp, old):
        shutil.rmtree(stale, ignore_errors=True)
    for hooks in sorted(overrides.glob("*/hooks")):
        shutil.copytree(hooks, tmp / hooks.parent.name / "hooks",
                        ignore=shutil.ignore_patterns("__pycache__"))
    if copy_root.exists():
        copy_root.rename(old)
    tmp.rename(copy_root)
    shutil.rmtree(old, ignore_errors=True)


def _sync(apply: bool) -> int:
    try:
        for w in check_config():
            print(f"WARN {w}")
        pending = [(key, cfg, root) for key, cfg, root in git_packs() if needs_fetch(cfg, root)]
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
    clashes = duplicate_packs(srcs) + collisions(srcs)
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
    bad_packs = pack_errors(srcs)
    if bad_packs:
        for _, errors in bad_packs:
            for e in errors:
                print(f"ERROR {e}")
        runs = ", ".join(f"`{config.command(f'validate --pack {tilde(src.root)}')}`" for src, _ in bad_packs)
        print(f"\nNothing written. Fix the pack ({runs} lists every problem), then re-run.")
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
    conflicts, changed, changes = 0, 0, len(pending)
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
            if link.copy:
                _copy_hooks(*link.copy)
            link.dest.parent.mkdir(parents=True, exist_ok=True)
            if link.dest.is_symlink():
                link.dest.unlink()
            link.dest.symlink_to(link.source)
    for p in stale:
        changes += 1
        print(f"{'PRUNE':9} {'':9} {tilde(p)}")
        if apply:
            p.unlink()
    copy = stale_hooks_copy(links)
    if copy:
        changes += 1
        print(f"{'PRUNE':9} {'':9} {tilde(copy)}")
        if apply:
            shutil.rmtree(copy)
    for m in merges:
        before = read_current(m.dest)
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
            try:
                write_settings(m.dest, merged, before)
            except FileChanged:
                changed += 1
                print(f"{'CHANGED':9} {m.harness:9} {tilde(m.dest)}  {CHANGED_HINT}")
    for s in mcp_plan(srcs):
        before = read_current(s.dest)
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
                try:
                    write_mcp(s, text, owned, before)
                except FileChanged:
                    changed += 1
                    print(f"{'CHANGED':9} {s.harness:9} {tilde(s.dest)}  {CHANGED_HINT}")
        elif apply:
            record_owned(s, owned)  # e.g. adopt entries that already match after lost state

    if not changes and not conflicts:
        print("Everything in sync.")
    elif not apply and changes:
        print("\nDry run. Run `apply` to write.")
    if conflicts:
        print(f"\n{conflicts} conflict(s): existing files not managed by this repo. "
              "Move them into the repo (or delete them), then re-run.")
    if changed:
        print(f"\n{changed} file(s) changed while apply ran, so they were left alone. "
              "Close Claude Code (it rewrites ~/.claude.json while running), then re-run.")
    return 1 if conflicts or changed else 0


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
    """The `brainrc` console script of an installed package."""
    sys.exit(main(sys.argv))


def main(argv: list[str]) -> int:
    """Run one command. A reader that stops early (`brainrc doctor | head`) ends it quietly."""
    try:
        code = _dispatch(argv)
        sys.stdout.flush()  # inside the try: a closed pipe fails here, not at interpreter exit
        return code
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())  # so the final flush can't fail
        return 0


def _dispatch(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "--version" and len(argv) == 2:
        print(f"brainrc {'.'.join(map(str, core_version()))}")
        return 0
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
    if cmd == "release" and len(argv) == 4 and argv[2] == "--notes":
        return cmd_release_notes(argv[3])
    if cmd == "doctor" and len(argv) == 2:
        return cmd_doctor()
    if cmd == "update" and len(argv) == 2:
        return cmd_update()
    if cmd == "tokens" and len(argv) == 2:
        return cmd_tokens()
    print(__doc__.replace("brainrc.py ", "brainrc ") if config.installed() else __doc__)
    return 2
