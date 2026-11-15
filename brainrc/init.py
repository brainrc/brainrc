"""init: first-run setup. Pick the harnesses to manage, and adopt existing instruction files.

`brainrc init` asks which installed harnesses brainrc should manage and writes the answer to
harnesses.local.toml, then whether to install each default pack (packs.local.toml). `--profile`
sets what this machine installs (brainrc.local.toml). A harness's instructions file (~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, ...)
that the user wrote would make apply report a CONFLICT, so init copies its text into
rules/adopted-<harness>.local.md (rendered into every harness's instructions) and moves the
original aside, leaving the path free for apply's link. Run from a project folder, it offers to
import that folder's CLAUDE.md, AGENTS.md, Cursor and Copilot files into a pack (#297), and asks
for a starter profile (brainrc/starter.py). It shows the file, hook and token counts before it
writes anything. It never runs apply itself.
"""
from __future__ import annotations

import os
import re
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import config, importers
from .config import (
    PROFILE_FILE, PROFILES, ConfigError, TABLE_HEADER, _layered, check_config, expand, harness_home,
    config_path, install_profile, load_harnesses, table_span, tilde, write_text_atomic,
)
from .plan import _managed_target, link_target
from .scaffold import write_pack
from .sources import default_packs, sources
from .starter import STARTER_HELP, STARTERS, always_tokens, hook_count, starter_text

IMPORT_NAME = "imported"  # the pack init imports the folder's instruction files into


@dataclass
class Adoption:
    harness: str
    file: Path  # the user's instructions file (or a link to one that brainrc didn't make)
    rule: Path | None  # the local rule that gets its text; None when it is empty or already adopted
    backup: Path  # where the original is moved
    text: str = ""  # what the rule gets
    note: str = ""  # why there is no rule: "it was empty" or "its text was already adopted"


def _ask(question: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        print(f"{question} {hint} ", end="", flush=True)
        line = sys.stdin.readline()
        if not line:  # end of input: take the default
            print()
            return default
        answer = line.strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer y or n.")


def set_enabled(text: str, name: str, value: bool) -> str:
    """text (a harnesses.local.toml) with `enabled` set for [name], everything else kept as is."""
    line = f"enabled = {'true' if value else 'false'}"
    lines = text.splitlines(keepends=True)
    span = table_span(lines, name)
    if span is None:  # a new table at the end, after one blank line
        head = text.rstrip("\n") + "\n\n" if text.strip() else ""
        return f"{head}[{name}]\n{line}\n"
    start, end = span
    for i in range(start + 1, end):
        if re.match(r"\s*[\"']?enabled[\"']?\s*=", lines[i]):
            lines[i] = line + "\n"
            return "".join(lines)
    if not lines[start].endswith("\n"):
        lines[start] += "\n"
    lines.insert(start + 1, line + "\n")
    return "".join(lines)


def set_profile(text: str, profile: str) -> str:
    """text (a brainrc.local.toml) with its top-level `profile` set, everything else kept as is."""
    line = f'profile = "{profile}"\n'
    lines = text.splitlines(keepends=True)
    for i, raw in enumerate(lines):
        if TABLE_HEADER.match(raw):
            break
        if re.match(r"\s*profile\s*=", raw):
            lines[i] = line
            return "".join(lines)
    return line + text


def _write(path: Path, before: str, after: str, dry_run: bool, what: str) -> None:
    if after == before:
        return
    tomllib.loads(after)  # the setters keep the file valid TOML; fail loudly if one ever doesn't
    if not dry_run:
        write_text_atomic(path, after)
    print(f"{'Would write' if dry_run else 'Wrote'} {tilde(path)}: {what}.")


def _instruction_files(names: list[str], roots: list[Path]) -> list[tuple[str, Path]]:
    """The chosen harnesses' instructions files that would make apply report a CONFLICT: a real
    file, or a link that brainrc didn't make."""
    found, paths = [], set()
    for name, h in load_harnesses(include_disabled=True).items():
        if name not in names or "instructions" not in h:
            continue
        path = expand(h["instructions"])
        if path in paths or (path.is_symlink() and _managed_target(link_target(path), roots)):
            continue
        if path.is_symlink() or path.is_file():
            found.append((name, path))
            paths.add(path)
    return found


def _rule_path(rules: Path, harness: str, body: str) -> Path | None:
    """Where the adopted text goes: rules/adopted-<harness>[-<n>].local.md. None when an adopted
    rule already holds this text (init run again on a restored file)."""
    for old in sorted(rules.glob("adopted-*.local.md")) if rules.is_dir() else []:
        if _adopted_body(old.read_text()) == body:
            return None
    n = 1
    while True:
        rule = rules / (f"adopted-{harness}.local.md" if n == 1 else f"adopted-{harness}-{n}.local.md")
        if not rule.exists():
            return rule
        n += 1


HEADER = re.compile(r"\A<!-- adopted from .* by brainrc init -->\n\n")


def _adopted_body(text: str) -> str:
    return HEADER.sub("", text).strip()


def plan_adoptions(names: list[str], roots: list[Path]) -> list[Adoption]:
    rules = config.local_dir() / "rules"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seen: set[str] = set()
    adoptions = []
    for harness, path in _instruction_files(names, roots):
        try:
            body = path.read_text().strip()
        except OSError:  # a dangling link: nothing to adopt, but it still blocks apply's link
            body = ""
        backup = path.with_name(f"{path.name}.bak-brainrc-{stamp}")
        rule = _rule_path(rules, harness, body) if body and body not in seen else None
        if not body:
            adoptions.append(Adoption(harness, path, None, backup, note="it was empty"))
        elif rule is None:
            adoptions.append(Adoption(harness, path, None, backup, note="its text was already adopted"))
        else:
            seen.add(body)
            text = f"<!-- adopted from {tilde(path)} by brainrc init -->\n\n{body}\n"
            adoptions.append(Adoption(harness, path, rule, backup, text))
    return adoptions


def _adopt(a: Adoption) -> None:
    if a.rule:
        a.rule.parent.mkdir(parents=True, exist_ok=True)
        a.rule.write_text(a.text)
    os.replace(a.file, a.backup)  # as rename on POSIX, also on Windows; a link is moved as the link; its target is never touched


def _choose(question: str, choices: list[str], default: str) -> str:
    while True:
        print(f"{question} [{'/'.join(c.upper() if c == default else c for c in choices)}] ", end="", flush=True)
        line = sys.stdin.readline()
        if not line:
            print()
            return default
        answer = line.strip().lower()
        if not answer:
            return default
        if answer in choices:
            return answer
        print(f"Please answer {', '.join(choices[:-1])} or {choices[-1]}.")


def _is_checkout(path: Path) -> bool:
    """A brainrc checkout: its own AGENTS.md is brainrc's, not the user's."""
    return path == config.REPO or ((path / "harnesses.toml").is_file() and (path / "brainrc" / "init.py").is_file())


def project_sources(cwd: Path, skip: set[Path]) -> list[tuple[str, Path]]:
    """Instruction files in the folder init runs from that `brainrc import` reads: CLAUDE.md,
    AGENTS.md, Cursor rules, Copilot instructions. None in HOME or a brainrc checkout, and none
    that init adopts as a harness instructions file."""
    cwd = cwd.resolve()
    if cwd == Path.home().resolve() or _is_checkout(cwd):
        return []
    return [(fmt, p) for fmt, p in importers.discover(cwd) if p.resolve() not in skip]


@dataclass
class Write:
    path: Path
    before: str
    after: str
    what: str


def cmd_init(yes: bool = False, harnesses: list[str] | None = None, adopt: bool = True,
             dry_run: bool = False, profile: str | None = None, starter: str | None = None,
             import_files: bool = False) -> int:
    """Pick harnesses (all installed ones with --yes, or the ones named), adopt instruction files,
    offer to import the folder's instruction files, and pick a starter profile. Shows the file, hook
    and token counts, and (when it asks) waits for a yes, before it writes anything."""
    try:
        defaults = default_packs()
        packs = _layered("packs")
        for w in check_config():
            print(f"WARN {w}")
        every = load_harnesses(include_disabled=True)
        enabled = load_harnesses(include_missing=True)
        managed = load_harnesses()
        srcs = sources()
        roots = [s.root for s in sources(include_disabled=True)]
        current_profile, current_exclude = install_profile()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    interactive = not yes and harnesses is None
    if interactive and not sys.stdin.isatty():
        print(f"ERROR init asks questions, and stdin isn't a terminal. Run `{config.command('init --yes')}` "
              "to take the defaults, or name the harnesses with --harness.")
        return 2
    for name in harnesses or []:
        if name not in every:
            print(f"ERROR --harness {name}: no such harness (known: {', '.join(every)})")
            return 2

    print("Harnesses:")
    for name, h in enabled.items():
        home = harness_home(h)
        state = "installed" if name in managed else f"not installed ({tilde(home)} not found)"
        print(f"  {name:12} {state}")
    if harnesses is not None:
        chosen = list(dict.fromkeys(harnesses))
    elif yes:
        chosen = list(managed)
    else:
        chosen = [n for n in managed if _ask(f"Manage {n}?")]

    local = config.local_dir() / "harnesses.local.toml"
    before = local.read_text() if local.is_file() else ""
    after = before
    for name in every:
        if name in chosen and name not in managed:
            after = set_enabled(after, name, True)  # named, but disabled or not detected
        elif name not in chosen and name in managed:
            after = set_enabled(after, name, False)
    tomllib.loads(after)  # set_enabled keeps the file valid TOML; fail loudly if it ever doesn't

    adoptions = plan_adoptions(chosen, roots) if adopt else []
    if adoptions and interactive:
        adoptions = [a for a in adoptions if _ask(
            f"{tilde(a.file)} would be a CONFLICT for apply. Move it to {a.backup.name}"
            + (f" and load its text from {tilde(a.rule)}?" if a.rule else "?"))]

    # Instruction files in this folder: imported into one pack, loaded in every session.
    found = project_sources(Path.cwd(), {f.resolve() for _, f in _instruction_files(chosen, roots)})
    imported, import_dest, import_note = None, importers.default_dest(IMPORT_NAME), ""
    if found:
        names = ", ".join(tilde(p) for _, p in found)
        if import_dest.is_dir() and any(import_dest.iterdir()):
            import_note = (f"Found {names}; {tilde(import_dest)} already has files, so init leaves them. "
                           f"`{config.command('import')} . --force` imports them again.")
        elif import_files or (interactive and _ask(
                f"Import {names} into a pack `{IMPORT_NAME}`, which every session then loads?", False)):
            try:
                imported = importers.plan(found, IMPORT_NAME)
            except ConfigError as e:
                print(f"ERROR {e}")
                return 1
            except (OSError, UnicodeDecodeError) as e:
                print(f"ERROR {importers.why(e)}")
                return 1
            if not imported.spec.rules and not imported.spec.skills:
                imported, import_note = None, f"Found {names}, but there is nothing in them to import."
        else:
            import_note = (f"Found {names} here. `{config.command('init --import')}` or "
                           f"`{config.command('import .')}` makes a pack of them.")

    packs_file = config.local_dir() / "packs.local.toml"
    packs_before = packs_file.read_text() if packs_file.is_file() else ""
    packs_after = packs_before
    packs_what = []
    for key in defaults if interactive else []:
        on = packs.get(key, {}).get("enabled", True)
        what = packs.get(key, {}).get("description", "")
        if _ask(f"Install the {key} pack{f' ({what})' if what else ''}?", on) != on:
            packs_after = set_enabled(packs_after, key, not on)
            packs_what.append(f"{key} {'off' if on else 'on'}")
    if imported:
        packs_after = importers.set_pack_path(packs_after, IMPORT_NAME, config_path(import_dest))
        packs_what.append(f"pack {IMPORT_NAME} added")

    if interactive and not profile and not starter:
        print("Starter profiles: " + "; ".join(f"{k}: {v}" for k, v in STARTER_HELP.items()) + ".")
        starter = _choose("Which starter profile?", list(STARTERS), "app")
    profile_file = config.local_dir() / PROFILE_FILE
    before_profile = profile_file.read_text() if profile_file.is_file() else ""
    after_profile = before_profile
    if starter:
        after_profile = starter_text(before_profile, starter)
        what_profile = f"this machine starts with the {starter} profile ({STARTERS[starter][0]})"
    elif profile:
        after_profile = set_profile(before_profile, profile)
        what_profile = f"this machine installs the {profile} profile"

    writes = [Write(local, before, after, f"brainrc manages {', '.join(chosen) or 'no harness'}"),
              Write(packs_file, packs_before, packs_after, "; ".join(packs_what)),
              Write(profile_file, before_profile, after_profile, what_profile if after_profile != before_profile else "")]
    changed = [w for w in writes if w.after != w.before]
    for w in changed:
        tomllib.loads(w.after)  # every setter keeps the file valid TOML; fail loudly if one ever doesn't

    # What apply will install afterwards, from these answers: shown before anything is written.
    new_profile, new_exclude = current_profile, current_exclude
    if after_profile != before_profile:  # the setters only write valid values
        data = tomllib.loads(after_profile)
        new_profile, new_exclude = data.get("profile", "full"), data.get("exclude", [])
    local_packs = tomllib.loads(packs_after)
    off = {k for k in defaults if not local_packs.get(k, {}).get("enabled", packs.get(k, {}).get("enabled", True))}
    kept = [s for s in srcs if s.key not in off]
    hooks = hook_count(kept, {n: every[n] for n in chosen}, new_profile)
    extra_rules = [a.text for a in adoptions if a.rule]
    extra_descriptions: list[str] = []
    if imported:
        extra_rules += [t for rel, t in imported.files.items() if rel.startswith("rules/")]
        extra_descriptions = [s.description for s in imported.spec.skills] if "items" in PROFILES[new_profile] else []
    rule_tokens, description_tokens = always_tokens(kept, new_profile, new_exclude, extra_rules, extra_descriptions)
    new_files = sum(1 for w in changed if not w.path.exists()) + sum(1 for a in adoptions if a.rule)
    new_files += len(imported.files) if imported else 0
    edited = sum(1 for w in changed if w.path.exists())
    for w in imported.warnings if imported else []:
        print(f"WARN {w}")
    print("\nBefore writing:")
    print(f"  files: {new_files} new, {edited} changed, {len(adoptions)} moved aside")
    print(f"  hooks: {sum(hooks.values())} after apply"
          + (f" ({', '.join(f'{n} {c}' for n, c in hooks.items())})" if hooks else "")
          + ("" if "hooks" in PROFILES[new_profile] else f" (the {new_profile} profile installs none)"))
    print(f"  tokens: ~{rule_tokens + description_tokens} loaded in every session "
          f"(rules {rule_tokens}, descriptions {description_tokens})")
    unfetched = [k for k in defaults if k not in off and not any(s.key == k for s in srcs)]
    if unfetched:
        print(f"  not counted: {', '.join(unfetched)}, which apply fetches first")
    if import_note:
        print(import_note)
    if interactive and not dry_run and (changed or adoptions or imported) and not _ask("Write these changes?"):
        print("Nothing written.")
        return 0

    verb = "Would write" if dry_run else "Wrote"
    if after != before:
        if not dry_run:
            write_text_atomic(local, after)
        print(f"{verb} {tilde(local)}: brainrc manages {', '.join(chosen) or 'no harness'}.")
    else:
        print(f"brainrc manages {', '.join(chosen) or 'no harness'}; {tilde(local)} needs no change.")
    for a in adoptions:
        if not dry_run:
            _adopt(a)
        moved = "Would move" if dry_run else "Moved"
        where = f"; its text loads from {tilde(a.rule)}" if a.rule else f"; {a.note}"
        print(f"{moved} {tilde(a.file)} to {a.backup.name}{where}.")
    if imported:
        if not dry_run:
            try:
                write_pack(import_dest, imported.files, sources=[p for _, p in imported.sources])
            except (ConfigError, OSError) as e:
                print(f"ERROR {e if isinstance(e, ConfigError) else importers.why(e)}")
                return 1
        print(f"{verb} {tilde(import_dest)}: {importers.summary(imported)}, from "
              + ", ".join(tilde(p) for _, p in imported.sources) + ".")
    for w in writes[1:]:
        if w.what:
            _write(w.path, w.before, w.after, dry_run, w.what)
    if any(a.rule for a in adoptions):
        print("Adopted text goes into the shared rules, so every harness brainrc manages loads it.")
    moved = {a.file for a in adoptions}
    for f in [f for _, f in _instruction_files(chosen, roots) if f not in moved]:
        print(f"Left {tilde(f)} in place: apply will report it as a CONFLICT until you move it.")
    if not dry_run:
        print(f"\nNext: `{config.command('status')}` to see the changes, then `{config.command('apply')}`.")
    return 0
