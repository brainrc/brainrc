"""doctor: diagnose this machine's install, read-only."""
from __future__ import annotations

import contextlib
import io
import tomllib
from pathlib import Path

from . import config
from .config import (
    ConfigError,
    KINDS,
    _layered,
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
    load_pack,
    pack_compat,
    render_extensions,
    render_instructions,
)
from .opencode import agents_format, rendered_agents
from .plan import FragmentError, Link, invalid_fragments, link_target, plan
from .settings import settings_change
from .validate import ROLES_FIX, check_roles_link, cmd_validate




Finding = tuple[str, str, str]  # (FAIL | WARN, what is wrong, how to fix it)


def _doctor_sources() -> tuple[list[Source], list[Source], list[Finding]]:
    """(sources apply would use, every source root incl. disabled or broken packs, findings).
    Each pack is checked on its own, so one broken pack doesn't hide the rest."""
    srcs, every_src, found = [Source("core", config.REPO)], [Source("core", config.REPO)], []
    try:
        core = core_version()
        packs = _layered("packs")
    except (ConfigError, tomllib.TOMLDecodeError) as e:
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


def doctor_findings() -> list[Finding]:
    """Everything wrong with this machine's install, each with its fix. Writes nothing."""
    srcs, every_src, found = _doctor_sources()
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
