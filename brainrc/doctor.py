"""doctor: diagnose this machine's install, read-only."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
from pathlib import Path

from . import config
from .config import (
    ConfigError,
    KINDS,
    _layered,
    check_config,
    command,
    expand,
    extensions_file,
    home_extensions_file,
    load_harnesses,
    rendered_instructions,
    tilde,
)
from .sources import (
    Source,
    _pack_root,
    collisions,
    core_version,
    duplicate_packs,
    load_pack,
    pack_compat,
    render_extensions,
    render_instructions,
)
from .opencode import agents_format, rendered_agents
from .packs import needs_fetch
from .plan import FragmentError, Link, invalid_fragments, link_target, plan
from .settings import _owned, settings_change
from .mcp import check_servers, mcp_change, mcp_plan
from .validate import ROLES_FIX, check_roles_link, cmd_validate




Finding = tuple[str, str, str]  # (FAIL | WARN, what is wrong, how to fix it)


def _doctor_sources() -> tuple[list[Source], list[Source], list[Finding]]:
    """(sources apply would use, every source root incl. disabled or broken packs, findings).
    Each pack is checked on its own, so one broken pack doesn't hide the rest."""
    srcs, every_src, found = [Source("core", config.REPO)], [Source("core", config.REPO)], []
    try:
        core = core_version()
        packs = _layered("packs")
    except ConfigError as e:
        return srcs, every_src, [("FAIL", str(e), "fix VERSION or packs.toml / packs.local.toml")]
    disable = "or set `enabled = false` for it in packs.local.toml"
    for key, cfg in packs.items():
        try:
            root = _pack_root(cfg, key)
        except ConfigError as e:
            found.append(("FAIL", str(e), f"set `path` or `git` in [{key}], {disable}"))
            continue
        if "git" in cfg and not root.exists():
            if cfg.get("enabled", True):
                found.append(("FAIL", f"pack {key}: not fetched yet from {cfg['git']}", command("apply")))
            continue
        if "git" in cfg and cfg.get("enabled", True) and (why := needs_fetch(cfg, root)):
            found.append(("FAIL", f"pack {key}: {why}", f"{command('apply')} fetches it"))
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
                          command(f"validate --pack {tilde(root)}")))
        srcs.append(src)
    found += [("FAIL", d, "change `name` in one pack's pack.toml, or set `enabled = false` for one in packs.local.toml")
              for d in duplicate_packs(srcs)]
    found += [("FAIL", c, "rename one of the pair, then apply") for c in collisions(srcs)]
    return srcs, every_src, found


def _render_findings(srcs: list[Source]) -> list[Finding]:
    found = []
    targets = [(rendered_instructions(), lambda: render_instructions(srcs)),
               (home_extensions_file(), lambda: render_extensions(srcs))]
    if extensions_file().parent.is_dir() and not config.installed():
        targets.append((extensions_file(), lambda: render_extensions(srcs)))
    targets += [(path, lambda text=text: text) for path, text in rendered_agents(srcs).items()]
    for path, render in targets:
        rel = tilde(path) if not path.is_relative_to(config.REPO) else str(path.relative_to(config.REPO))
        if not path.is_file():
            found.append(("FAIL", f"{rel} has not been rendered", command("apply")))
        elif path.read_text() != render():
            found.append(("FAIL", f"{rel} is stale (sources changed since the last apply)", command("apply")))
    return found


def _link_finding(link: Link, roots: list[Path]) -> Finding | None:
    state, dest = link.state(roots), tilde(link.dest)
    if state == "create":
        return "FAIL", f"{link.harness}: {dest} is missing", command("apply")
    if state == "update":
        return "FAIL", f"{link.harness}: {dest} points at the wrong item", command("apply")
    if state == "ok":
        return None
    if not link.dest.is_symlink():
        return ("FAIL", f"{link.harness}: {dest} is a real file, not a link",
                f"move it into the repo or a pack (or delete it), then {command('apply')}")
    target = link_target(link.dest)
    if not target.exists():
        return ("FAIL", f"{link.harness}: {dest} is a broken link to {tilde(target)} (repo moved?)",
                f"rm {dest} && {command('apply')}")
    return ("FAIL", f"{link.harness}: {dest} links to {tilde(target)}, outside ai-config and its packs",
            f"move that into a pack (or delete the link), then {command('apply')}")


def _home_findings() -> list[Finding]:
    """WARN when the settings home is a legacy dir or AICFG_HOME, or an unused old dir remains."""
    found, origin, home = [], config.home_origin(), config.aicfg_home()
    if origin == "legacy":
        found.append(("WARN", f"settings home is the legacy {tilde(home)}", command("migrate")))
    elif origin == "aicfg_env":
        found.append(("WARN", f"settings home comes from the deprecated AICFG_HOME ({tilde(home)})",
                      f"set BRAINRC_HOME={tilde(config.new_home())} and run `{command('migrate')}`"))
    home_has_content = home.is_dir() and any(home.iterdir())
    for old in config.former_homes():
        if not old.exists():
            continue
        if home_has_content:
            found.append(("WARN", f"{tilde(old)} is unused (settings home is {tilde(home)})",
                          f"move anything you still need from it into {tilde(home)}, then remove it: rm -r {tilde(old)}"))
        else:  # the old dir may hold the only settings: move them, don't delete them
            found.append(("WARN", f"{tilde(old)} holds settings, but the settings home is {tilde(home)}",
                          f"`{command('migrate')}` moves it there"))
    return found


PLUGIN_LIST_MAX = 1024 * 1024  # bytes; a real installed_plugins.json is a few KB


def _plugin_findings() -> list[Finding]:
    """WARN when the old `ai-config` plugin is installed in Claude Code or Cursor. Read-only."""
    found, home = [], Path.home()
    installed = home / ".claude" / "plugins" / "installed_plugins.json"
    try:
        if installed.stat().st_size > PLUGIN_LIST_MAX:
            raise ValueError("implausibly large")
        data = json.loads(installed.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError, MemoryError):
        data = None  # missing, unreadable, huge, too deeply nested, or not JSON
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if isinstance(plugins, dict) and "ai-config@ai-config" in plugins:
        found.append(("WARN", f"the old plugin ai-config@ai-config is installed in Claude Code ({tilde(installed)})",
                      "run `/plugin uninstall ai-config@ai-config`, then `/plugin marketplace remove ai-config`, "
                      "then install brainrc@brainrc"))
    old = home / ".cursor" / "plugins" / "local" / "ai-config"
    try:
        has_old = old.is_symlink() or old.exists()
    except OSError:  # e.g. the parent isn't searchable
        has_old = False
    if has_old:
        found.append(("WARN", f"{tilde(old)} is the old ai-config plugin for Cursor",
                      f"remove the link (or directory) at {tilde(old)}, "
                      "then link the repo as ~/.cursor/plugins/local/brainrc"))
    return found


def doctor_findings() -> list[Finding]:
    """Everything wrong with this machine's install, each with its fix. Writes nothing."""
    try:
        warnings = check_config()
    except ConfigError as e:  # everything below reads this config, so stop here
        return [("FAIL", str(e), "fix that line in the file named")]
    srcs, every_src, found = _doctor_sources()
    found += [("WARN", w, "fix the name, or delete it if it isn't needed") for w in warnings]
    if roles := check_roles_link():
        found.append(("FAIL", roles, ROLES_FIX))
    try:
        for h in load_harnesses().values():
            agents_format(h)
    except ConfigError as e:  # renders and links depend on it, so stop here
        return found + [("FAIL", str(e), "set agents_format to claude or opencode in harnesses.local.toml")]
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
                          command("apply")))
        else:
            found += [_link_finding(link, roots) for link in group]
    found += [("FAIL", f"{tilde(p)} is a stale link ai-config no longer makes", f"{command('apply')} (prunes it)")
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

    found += [("FAIL", e, f"fix the JSON, then {command('apply')}") for e in invalid_fragments(srcs)]
    for m in merges:
        if m.harness in skipped:
            continue
        try:
            state, _ = settings_change(m)
        except FragmentError:
            continue  # reported above
        if state == "merge" and not m.fragments:
            found.append(("FAIL", f"{tilde(m.dest)} has ai-config's hooks but {m.harness} is disabled",
                          f"{command('apply')} (removes them)"))
        elif state == "merge":
            found.append(("FAIL", f"{m.harness}: {tilde(m.dest)} is missing ai-config's hooks", command("apply")))
        elif state == "conflict":
            found.append(("FAIL", f"{m.harness}: {tilde(m.dest)} is invalid JSON",
                          f"fix it by hand, then {command('apply')}"))
    found += _hook_findings(merges, skipped)
    found += _mcp_findings(srcs, skipped)
    found += _home_findings()
    found += _plugin_findings()
    return found


HOOK_SCRIPT = re.compile(r'"([^"]+\.py)"')  # the script in a `python3 "<dir>/<guard>.py"` command


def _hook_findings(merges: list, skipped: set[str]) -> list[Finding]:
    """ai-config's hooks in each settings file: the script exists and passes an empty payload.
    A missing script is skipped by the hook command, so its guard is silently off."""
    found = []
    for m in merges:
        if m.harness in skipped or not m.fragments or not m.dest.is_file():
            continue
        try:
            current = json.loads(m.dest.read_text())
        except json.JSONDecodeError:
            continue  # reported with the settings checks
        scripts: dict[Path, int] = {}
        for groups in current.get("hooks", {}).values():
            for group in groups:
                if not _owned(group, m.markers()):
                    continue
                for h in [group, *group.get("hooks", [])]:
                    match = HOOK_SCRIPT.search(str(h.get("command", "")))
                    if match:
                        scripts.setdefault(Path(os.path.expandvars(match[1])), h.get("timeout", 5))
        for script, timeout in scripts.items():
            hook = f"{m.harness}: hook {tilde(script)}"
            if not script.is_file():
                found.append(("FAIL", f"{m.harness}: hook missing: {tilde(script)}", command("apply")))
                continue
            try:  # -B: doctor is read-only, so no __pycache__ next to the guards
                result = subprocess.run(["python3", "-B", str(script)], input="{}", capture_output=True,
                                        text=True, timeout=timeout)
            except FileNotFoundError:
                found.append(("FAIL", f"{hook} can't run: python3 is not on PATH", "install Python 3"))
                continue
            except subprocess.TimeoutExpired:
                found.append(("FAIL", f"{hook} timed out after {timeout}s", f"run `python3 {tilde(script)}`"))
                continue
            if result.returncode:
                found.append(("FAIL", f"{hook} exits {result.returncode} on an empty payload",
                              f"run `python3 {tilde(script)}` to see why, then {command('apply')}"))
    return found


def _mcp_findings(srcs: list[Source], skipped: set[str]) -> list[Finding]:
    if errors := check_servers(srcs):
        return [("FAIL", e, f"fix mcp/servers.toml, then {command('apply')}") for e in errors]
    found = []
    for s in mcp_plan(srcs):
        if s.harness in skipped:
            continue
        state, _, clashing, _ = mcp_change(s)
        found += [("WARN", f"{s.harness}: your own MCP server `{n}` in {tilde(s.dest)} shadows ai-config's",
                   f"rename or remove yours, then {command('apply')}") for n in clashing]
        if state == "invalid":
            found.append(("FAIL", f"{s.harness}: {tilde(s.dest)} can't be parsed, so its MCP servers aren't synced",
                          f"fix it by hand, then {command('apply')}"))
        elif state == "merge":
            found.append(("FAIL", f"{s.harness}: {tilde(s.dest)} doesn't match ai-config's MCP servers",
                          command("apply")))
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
