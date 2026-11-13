"""brainrc: sync this repo's skills, agents, commands, rules, and hooks into AI harnesses.

Sources are this repo ("core", versioned by VERSION) plus any packs listed in packs.toml /
packs.local.toml, by `path` or by `git` URL (docs/packs.md). The commands and their options are
built in `_parser`; `brainrc --help` and `brainrc <command> --help` print them.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from . import config
from .config import (
    ConfigError,
    check_config,
    home_extensions_file,
    legacy_extensions,
    legacy_instructions,
    rendered_agents_dir,
    rendered_instructions,
    settings_home,
    tilde,
)
from .sources import (
    check_packs, collisions, core_version, duplicate_packs, render_instructions, sources,
)
from .init import cmd_init
from .uninstall import cmd_uninstall
from .opencode import rendered_agents
from .packs import adopt_record, describe, fetch_pack, git_packs, needs_fetch
from .plan import hooks_copy_current, invalid_fragments, link_target, old_root, plan, stale_hooks_copy
from .mcp import check_servers, mcp_change, mcp_plan, record_owned, write_mcp
from .settings import FileChanged, read_current, settings_change, write_settings
from .plugin import cmd_plugin
from .plugins import render_extensions
from .release import cmd_release, cmd_release_notes
from .tokens import cmd_tokens
from .validate import cmd_validate, pack_errors
from .doctor import cmd_doctor
from .manifest import checked_manifest, updated_manifest, write_manifest
from .moved import move_warnings
from .migrate import cmd_migrate
from .project import MANIFEST as PROJECT_MANIFEST, find_project, sync as project_sync
from . import frozen as frozen_install
from . import lock


CHANGED_HINT = "(changed during apply; close Claude Code and re-run)"


def cmd_sync(apply: bool, only: list[str] | None = None, repair: bool = False) -> int:
    """status (apply=False) or apply; apply holds the settings home's apply.lock while it runs.
    `only` limits links, settings and MCP merges to those harnesses; the rest are left as they are.
    `repair` relinks links into a moved checkout or an old package path (see Link.state)."""
    if only:
        try:
            unknown = config.check_only(only)
        except ConfigError as e:  # a broken harnesses.toml: the same error and exit as without --only
            print(f"ERROR {e}")
            return 1
        if unknown:
            print(f"ERROR {unknown}")
            return 2
    with config.only_harnesses(only):
        return _locked_sync(apply, repair)


def _locked_sync(apply: bool, repair: bool = False) -> int:
    return _locked(lambda: _both_scopes(True, repair)) if apply else _both_scopes(False, repair)


def _both_scopes(apply: bool, repair: bool = False) -> int:
    """User scope, then the project in the current directory, if it has a brainrc.toml."""
    code = _sync(apply, repair)
    root = find_project()
    return max(code, project_sync(root, apply)) if root else code


def _locked(run) -> int:
    """run() while holding the settings home's apply.lock, so apply and uninstall never overlap."""
    lock = settings_home() / "apply.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "a") as f:
        if not _try_lock(f):
            print(f"ERROR another brainrc apply is running (lock: {tilde(lock)})")
            print("\nNothing written. Let it finish, then re-run.")
            return 1
        return run()


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
    tmp = copy_root.with_name(f".{copy_root.name}.brainrc-tmp-{os.getpid()}")
    old = copy_root.with_name(f".{copy_root.name}.brainrc-old-{os.getpid()}")
    for stale in (tmp, old):
        shutil.rmtree(stale, ignore_errors=True)
    for hooks in sorted(overrides.glob("*/hooks")):
        shutil.copytree(hooks, tmp / hooks.parent.name / "hooks",
                        ignore=shutil.ignore_patterns("__pycache__"))
    if copy_root.exists():
        copy_root.rename(old)
    tmp.rename(copy_root)
    shutil.rmtree(old, ignore_errors=True)


def _old_roots(srcs, roots: list[Path]) -> tuple[list[Path], list[Path]]:
    """apply --repair: (source roots apply recorded before, roots whose stale links may be pruned).

    A recorded root is trusted: links into it are repaired, and stale ones pruned. A root inferred
    from a broken link (an install from before the manifest) only adds pruning, and only when it no
    longer exists and isn't ~, / or one of ~'s ancestors, so a live link of the user's is never
    taken for brainrc's. The broken link itself is repaired as a moved item either way."""
    manifest, warnings = checked_manifest()
    for w in warnings:
        print(f"WARN {w}")
    trusted = [Path(r) for r in manifest["roots"] if Path(r) not in roots]
    prune = list(trusted)
    home = Path.home()
    for link in plan(srcs)[0]:
        if link.state(roots, trusted) == "repair" and (root := old_root(link_target(link.dest), link.source, roots)):
            if not os.path.lexists(root) and root != home and root not in home.parents:
                prune.append(root)
    return trusted, list(dict.fromkeys(prune))


def _sync(apply: bool, repair: bool = False, relock: bool = True) -> int:
    try:
        for w in check_config():
            print(f"WARN {w}")
        packs = git_packs()
        pending = [(key, cfg, root) for key, cfg, root in packs if needs_fetch(cfg, root)]
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    if apply:
        for key, cfg, root in packs:
            adopt_record(cfg, root)
    for key, cfg, root in pending:
        print(describe(key, cfg))
        if apply:
            try:
                fetch_pack(key, cfg, root)
            except ConfigError as e:
                print(f"ERROR {e}")
                print(f"\nNothing written. Check the pack's `git` and `ref`, then re-run, or set "
                      f"`enabled = false` for [{key}] in packs.local.toml.")
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
    try:
        bad_packs = pack_errors(srcs)
        extensions = render_extensions(srcs)
    except ConfigError as e:  # a pack's validator that won't load or run
        print(f"ERROR {e}\n\nNothing written. Fix the pack's validator, or disable the pack.")
        return 1
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
        if extensions is not None:
            home_extensions_file().write_text(extensions)
        elif home_extensions_file().is_file():  # no enabled pack reads it any more
            home_extensions_file().unlink()
        for path, text in agents.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        if rendered_agents_dir().is_dir():
            for old in rendered_agents_dir().glob("*.md"):
                if old not in agents:
                    old.unlink()
        if not config.installed() and legacy_extensions().is_file():  # left behind by the move to packs/
            legacy_extensions().unlink()
            for d in legacy_extensions().parents[:3]:  # references/, spec-agent/, skills/, if now empty
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()
        if not config.installed() and legacy_instructions().is_file():
            legacy_instructions().unlink()
            if not any(legacy_instructions().parent.iterdir()):
                legacy_instructions().parent.rmdir()

    old, prune = _old_roots(srcs, roots) if repair else (None, None)
    links, stale, merges = plan(srcs, old_roots=prune)
    conflicts, changed, changes, repairable = 0, 0, len(pending), 0
    for link in links:
        state = link.state(roots, old)
        if state == "ok":
            continue
        print(f"{state.upper():9} {link.harness:9} {tilde(link.dest)}")
        if state == "conflict":
            conflicts += 1
            repairable += link.state(roots, []) == "repair"
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
    copy = stale_hooks_copy(links) if config.harness_scope() is None else None
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
                  "rename it or remove it to let brainrc manage it)")
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

    managed = {n: h for n, h in config.load_harnesses().items() if config.in_scope(n)}
    for w in move_warnings(managed):
        print(f"WARN {w}")
    lock_code = _user_lock(srcs, apply and relock)
    if apply:
        write_manifest(updated_manifest(managed, [s.root for s in srcs], config.harness_scope()))
    missing = {n: home for n, home in config.missing_harnesses().items() if config.in_scope(n)}
    if missing:
        names = ", ".join(f"{n} ({tilde(home)})" for n, home in missing.items())
        print(f"Skipped, not installed: {names}. To manage one anyway, set `enabled = true` "
              "for it in harnesses.local.toml.")
    if not changes and not conflicts:
        print("Everything in sync.")
    elif not apply and changes:
        print("\nDry run. Run `apply` to write.")
    if conflicts:
        print(f"\n{conflicts} conflict(s): existing files not managed by this repo. "
              "Move them into the repo (or delete them), then re-run.")
        if repairable:
            print(f"{repairable} of them are broken links to where an item used to be (a moved checkout?): "
                  f"`{config.command('apply --repair')}` relinks them.")
    if changed:
        print(f"\n{changed} file(s) changed while apply ran, so they were left alone. "
              f"Close Claude Code (it rewrites {tilde(config.claude_json())} while running), then re-run.")
    return 1 if conflicts or changed or lock_code else 0


def _user_lock(srcs, apply: bool) -> int:
    """apply writes the user scope's brainrc.lock; both report a ref that moved to another commit."""
    path = lock.user_lock_path()
    try:
        old = lock.read(path)
        new = lock.user_lock(srcs)
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    lock.report_moved(old, new, "apply relocks it" if not apply else f"relocked in {tilde(path)}")
    if apply:
        lock.write(path, new)
    return 0


def cmd_install(frozen: bool, scope: str | None = None) -> int:
    """install = apply. install --frozen installs exactly what the lock records (brainrc/frozen.py):
    the project's when the current directory has one (or --scope project), else the user scope's."""
    if not frozen:
        return cmd_sync(apply=True)
    root = find_project()
    scope = scope or ("project" if root else "user")
    if scope == "project" and root is None:
        print(f"ERROR no {PROJECT_MANIFEST} here or above, up to the repo root")
        return 2
    if scope == "project":
        return _locked(lambda: frozen_install.project(root))
    return _locked(lambda: frozen_install.user(lambda: _sync(True, relock=False)))


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


def refuse_unmigrated() -> int | None:
    """status, apply and update stop here, writing nothing, while an old home is unmigrated."""
    old = config.unmigrated_home()
    if not old:
        return None
    kind, path = old
    if kind == "env":
        print(f"ERROR AICFG_HOME is no longer read: set BRAINRC_HOME={config.tilde(config.new_home())} "
              "and run brainrc migrate")
    else:
        print(f"ERROR {config.tilde(path)} is no longer read: run brainrc migrate "
              f"to move it to {config.tilde(config.new_home())}")
    return 1


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


SUMMARY = "Sync skills, agents, commands, rules, hooks and MCP servers into AI coding harnesses."

EPILOG = """\
Sources: this repo ("core") plus the packs in packs.toml / packs.local.toml (docs/packs.md).
Safety: brainrc never overwrites a file or a link it doesn't manage. Those are reported as
CONFLICT and left alone; settings and MCP files are merged and backed up first."""


class _Formatter(argparse.RawDescriptionHelpFormatter):
    """Keeps the epilog's line breaks, and leaves hidden commands out of the command list."""

    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            action._choices_actions = [a for a in action._choices_actions if a.help != argparse.SUPPRESS]
        return super()._format_action(action)


def _harness_list(value: str) -> list[str]:
    return [n.strip() for n in value.split(",") if n.strip()]


def _parser() -> argparse.ArgumentParser:
    prog = config.command("").strip()
    parser = argparse.ArgumentParser(prog=prog, description=SUMMARY, epilog=EPILOG,
                                     formatter_class=_Formatter)
    parser.add_argument("--version", action="store_true", help="print `brainrc <VERSION>` and exit")
    sub = parser.add_subparsers(dest="cmd", metavar="<command>", title="commands")

    def add(name: str, help: str, description: str | None = None, hidden: bool = False):
        return sub.add_parser(name, help=argparse.SUPPRESS if hidden else help,
                              description=description or help)

    p = add("init", "first run: pick the harnesses to manage, and adopt their existing instruction "
            "files", "Ask which installed harnesses brainrc should manage and write the answer to "
            "harnesses.local.toml. A harness instructions file you wrote (~/.claude/CLAUDE.md, "
            "~/.codex/AGENTS.md, ...) would be a CONFLICT for apply, so init copies its text into "
            "rules/adopted-<harness>.local.md, which every harness loads, and moves the original "
            "aside as <file>.bak-brainrc-<time>. It doesn't run apply.")
    p.add_argument("--yes", "-y", action="store_true",
                   help="ask nothing: manage every installed harness and adopt every instruction file")
    p.add_argument("--harness", action="append", type=_harness_list, metavar="HARNESS",
                   help="manage exactly these harnesses (repeat it, or separate names with commas); "
                   "asks nothing")
    p.add_argument("--no-adopt", action="store_true", help="leave instruction files where they are")
    p.add_argument("--profile", choices=("minimal", "recommended", "full"),
                   help="what this machine installs, in brainrc.local.toml: minimal is rules only, "
                   "recommended adds skills, agents, commands and hooks, full adds MCP servers")
    p.add_argument("--dry-run", action="store_true", help="print what init would do, write nothing")
    repair_help = ("also relink broken links to where an item used to be: after moving the checkout, "
                   "or a package upgrade to a new Python")
    only_help = ("only these harnesses (repeat it, or separate names with commas); the others "
                 "are left as they are")
    p = add("status", "show what apply would change (the default command; writes nothing)")
    p.add_argument("--only", action="append", type=_harness_list, metavar="HARNESS", help=only_help)
    p.add_argument("--repair", action="store_true", help=repair_help)
    p = add("apply", "render rules and pack extensions, link items, merge settings and MCP servers",
            "Render rules and pack extensions to the settings home ($BRAINRC_HOME, default "
            "~/.config/brainrc), create or refresh the links in each harness, and merge hooks and "
            "MCP servers (mcp/servers.toml) into its settings files.")
    p.add_argument("--only", action="append", type=_harness_list, metavar="HARNESS", help=only_help)
    p.add_argument("--repair", action="store_true", help=repair_help)
    add("update", "refetch packs named by `git` URL at their `ref`, then apply")
    p = add("install", "apply; with --frozen, install exactly what brainrc.lock records",
            "Without --frozen, the same as apply. With --frozen, install exactly what brainrc.lock "
            "records: each git pack at its locked commit (never its ref), every file checked against "
            "its hash. Any difference between the config, the lock and the packs fails, names the "
            "item and writes nothing. In a repo with brainrc.toml it installs the project's lock; "
            "elsewhere the user scope's ($BRAINRC_HOME/brainrc.lock).")
    p.add_argument("--frozen", action="store_true", help="install exactly what brainrc.lock records, or fail")
    p.add_argument("--scope", choices=("user", "project"),
                   help="which lock --frozen installs (default: the project's when there is one)")
    p = add("uninstall", "remove everything apply put into the harnesses",
            "Remove the links brainrc made (broken ones too), its hooks in each settings file and "
            "the MCP servers it added, then the files and directories that leaves empty. Your own "
            "settings, hooks and servers stay, and an instructions file `init` moved aside is put "
            "back. It works after the checkout is moved or deleted.")
    p.add_argument("--dry-run", action="store_true", help="print what uninstall would remove, write nothing")
    p.add_argument("--purge", action="store_true",
                   help="also delete the settings home ($BRAINRC_HOME): local config, rendered files and "
                   "fetched git packs")
    p = add("validate", "check frontmatter, cross-references, packs and tripwires (CI runs it)")
    p.add_argument("--pack", metavar="DIR", help="check core plus this pack only")
    add("doctor", "diagnose this machine's install (read-only); exits 1 on any problem, each "
        "with its fix")
    p = add("migrate", "move an old settings home (AICFG_HOME or ~/.config/ai-config) to "
            "BRAINRC_HOME, then apply; refuses a non-empty target")
    p.add_argument("--dry-run", action="store_true", help="only print the move")
    add("tokens", "estimate the context cost of every skill, agent and command")
    add("plugin", "write the plugin manifests (.claude-plugin/, plugin.json)", hidden=True)
    p = add("release", "fold changelog.d/ into CHANGELOG.md, bump VERSION, rewrite the manifests",
            hidden=True)
    group = p.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="print the release, write nothing")
    group.add_argument("--notes", metavar="X.Y.Z", help="print that version's CHANGELOG.md section")
    return parser


def _dispatch(argv: list[str]) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv[1:])
    except SystemExit as e:  # --help exits 0, a usage error 2
        return e.code if isinstance(e.code, int) else 2
    if args.version:
        if args.cmd:
            parser.print_usage(sys.stderr)
            print(f"{parser.prog}: error: --version takes no command", file=sys.stderr)
            return 2
        print(f"brainrc {'.'.join(map(str, core_version()))}")
        return 0
    cmd = args.cmd or "status"
    if cmd == "migrate":
        return cmd_migrate(dry_run=args.dry_run)
    if cmd in ("init", "status", "apply", "update", "install", "uninstall") and (code := refuse_unmigrated()):
        return code
    if cmd == "uninstall":
        if args.dry_run:
            return cmd_uninstall(dry_run=True, purge=args.purge)
        if not settings_home().exists():  # nothing to lock against, and the lock would create it
            return cmd_uninstall(purge=args.purge)
        return _locked(lambda: cmd_uninstall(purge=args.purge))
    if cmd == "init":
        named = [n for names in args.harness or [] for n in names] if args.harness else None
        return cmd_init(yes=args.yes, harnesses=named, adopt=not args.no_adopt, dry_run=args.dry_run,
                        profile=args.profile)
    if cmd in ("status", "apply"):
        only = [n for names in getattr(args, "only", None) or [] for n in names]
        return cmd_sync(apply=cmd == "apply", only=only or None, repair=args.repair)
    if cmd == "validate":
        return cmd_validate(args.pack) if args.pack else cmd_validate()
    if cmd == "plugin":
        return cmd_plugin()
    if cmd == "release":
        return cmd_release_notes(args.notes) if args.notes else cmd_release(dry_run=args.dry_run)
    if cmd == "doctor":
        return cmd_doctor()
    if cmd == "update":
        return cmd_update()
    if cmd == "install":
        if args.scope and not args.frozen:
            print("ERROR --scope needs --frozen", file=sys.stderr)
            return 2
        return cmd_install(args.frozen, args.scope)
    return cmd_tokens()
