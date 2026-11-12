"""init: first-run setup. Pick the harnesses to manage, and adopt existing instruction files.

`brainrc init` asks which installed harnesses brainrc should manage and writes the answer to
harnesses.local.toml, then whether to install each default pack (packs.local.toml). `--profile`
sets what this machine installs (brainrc.local.toml). A harness's instructions file (~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, ...)
that the user wrote would make apply report a CONFLICT, so init copies its text into
rules/adopted-<harness>.local.md (rendered into every harness's instructions) and moves the
original aside, leaving the path free for apply's link. It never runs apply itself.
"""
from __future__ import annotations

import os
import re
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .config import (
    PROFILE_FILE, ConfigError, TABLE_HEADER, _layered, check_config, expand, harness_home, load_harnesses, tilde,
)
from .plan import _managed_target, link_target
from .sources import default_packs, sources


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
    start = next((i for i, raw in enumerate(lines)
                  if (m := TABLE_HEADER.match(raw)) and m[1].strip("\"'") == name), None)
    if start is None:  # a new table at the end, after one blank line
        head = text.rstrip("\n") + "\n\n" if text.strip() else ""
        return f"{head}[{name}]\n{line}\n"
    end = next((i for i in range(start + 1, len(lines)) if TABLE_HEADER.match(lines[i])), len(lines))
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
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(after)
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
    os.rename(a.file, a.backup)  # a link is moved as the link; its target is never touched


def cmd_init(yes: bool = False, harnesses: list[str] | None = None, adopt: bool = True,
             dry_run: bool = False, profile: str | None = None) -> int:
    """Pick harnesses (all installed ones with --yes, or the ones named) and adopt instruction files."""
    try:
        defaults = default_packs()
        packs = _layered("packs")
        for w in check_config():
            print(f"WARN {w}")
        every = load_harnesses(include_disabled=True)
        enabled = load_harnesses(include_missing=True)
        managed = load_harnesses()
        roots = [s.root for s in sources(include_disabled=True)]
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

    verb = "Would write" if dry_run else "Wrote"
    if after != before:
        if not dry_run:
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(after)
        print(f"{verb} {tilde(local)}: brainrc manages {', '.join(chosen) or 'no harness'}.")
    else:
        print(f"brainrc manages {', '.join(chosen) or 'no harness'}; {tilde(local)} needs no change.")
    for a in adoptions:
        if not dry_run:
            _adopt(a)
        moved = "Would move" if dry_run else "Moved"
        where = f"; its text loads from {tilde(a.rule)}" if a.rule else f"; {a.note}"
        print(f"{moved} {tilde(a.file)} to {a.backup.name}{where}.")
    packs_file = config.local_dir() / "packs.local.toml"
    packs_before = packs_file.read_text() if packs_file.is_file() else ""
    packs_after = packs_before
    for key in defaults if interactive else []:
        on = packs.get(key, {}).get("enabled", True)
        what = packs.get(key, {}).get("description", "")
        if _ask(f"Install the {key} pack{f' ({what})' if what else ''}?", on) != on:
            packs_after = set_enabled(packs_after, key, not on)
    _write(packs_file, packs_before, packs_after, dry_run, "default packs changed")
    if profile:
        profile_file = config.local_dir() / PROFILE_FILE
        before_profile = profile_file.read_text() if profile_file.is_file() else ""
        _write(profile_file, before_profile, set_profile(before_profile, profile), dry_run,
               f"this machine installs the {profile} profile")
    if any(a.rule for a in adoptions):
        print("Adopted text goes into the shared rules, so every harness brainrc manages loads it.")
    moved = {a.file for a in adoptions}
    for f in [f for _, f in _instruction_files(chosen, roots) if f not in moved]:
        print(f"Left {tilde(f)} in place: apply will report it as a CONFLICT until you move it.")
    if not dry_run:
        print(f"\nNext: `{config.command('status')}` to see the changes, then `{config.command('apply')}`.")
    return 0
