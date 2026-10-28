"""Release: fold changelog.d/ fragments into CHANGELOG.md and bump VERSION.

Each PR adds one fragment instead of editing VERSION and CHANGELOG.md, so open PRs don't
conflict. The release workflow runs `release` on every merge to main, then tags the result.
"""
from __future__ import annotations

import datetime
import re

from . import config
from .config import CHANGELOG_VERSION, ConfigError
from .plugin import cmd_plugin
from .sources import core_version

FRAGMENTS = "changelog.d"
BUMPS = ("patch", "minor", "major")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


def fragment_paths() -> list:
    d = config.REPO / FRAGMENTS
    return sorted(p for p in d.glob("*.md") if p.name != "README.md") if d.is_dir() else []


def parse_fragment(text: str, rel: str) -> tuple[str, str]:
    """(bump, entry) from `---\\nbump: patch\\n---\\n- entry`."""
    m = FRONTMATTER.match(text)
    if not m:
        raise ConfigError(f"{rel}: needs frontmatter `---` / `bump: patch|minor|major` / `---`")
    fields = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    bump = fields.get("bump", "").strip()
    if bump not in BUMPS:
        raise ConfigError(f"{rel}: `bump` must be one of {', '.join(BUMPS)}, got `{bump}`")
    entry = m.group(2).strip()
    if not entry.startswith("- "):
        raise ConfigError(f"{rel}: the entry must be a changelog bullet starting with `- `")
    return bump, entry


def check_fragments() -> list[str]:
    errors = []
    for p in fragment_paths():
        try:
            parse_fragment(p.read_text(), f"{FRAGMENTS}/{p.name}")
        except ConfigError as e:
            errors.append(str(e))
    return errors


def next_version(core: tuple[int, ...], bump: str) -> tuple[int, ...]:
    major, minor, patch = core
    if bump == "major":
        return major + 1, 0, 0
    if bump == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def cmd_release(dry_run: bool = False) -> int:
    """Bump VERSION by the largest fragment bump, prepend the entries, delete the fragments."""
    if config.installed():
        print("ERROR release edits the repo; run it from a checkout: python3 scripts/brainrc.py release")
        return 1
    paths = fragment_paths()
    if not paths:
        print(f"No fragments in {FRAGMENTS}/: nothing to release.")
        return 0
    try:
        parsed = [parse_fragment(p.read_text(), f"{FRAGMENTS}/{p.name}") for p in paths]
        core = core_version()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    bump = max((b for b, _ in parsed), key=BUMPS.index)
    version = ".".join(map(str, next_version(core, bump)))
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    section = f"## {version} ({today})\n\n" + "\n".join(entry for _, entry in parsed) + "\n\n"
    print(f"{'Would release' if dry_run else 'Releasing'} {version} ({bump}) from {len(paths)} fragment(s)")
    if dry_run:
        print(section, end="")
        return 0
    changelog = config.REPO / "CHANGELOG.md"
    text = changelog.read_text()
    m = CHANGELOG_VERSION.search(text)
    at = m.start() if m else len(text)
    changelog.write_text(text[:at] + section + text[at:])
    (config.REPO / "VERSION").write_text(version + "\n")
    for p in paths:
        p.unlink()
    return cmd_plugin()


def release_notes(text: str, version: str) -> str | None:
    """The body of CHANGELOG.md's `## <version>` section, stripped; None if there is none."""
    head = re.search(rf"^## {re.escape(version)}\b.*$", text, re.M)
    if not head:
        return None
    end = CHANGELOG_VERSION.search(text, head.end())
    return text[head.end():end.start() if end else len(text)].strip()


def cmd_release_notes(version: str) -> int:
    """Print a version's changelog section: the body of its GitHub Release (read-only)."""
    notes = release_notes((config.REPO / "CHANGELOG.md").read_text(), version)
    if notes is None:
        print(f"ERROR CHANGELOG.md has no section for {version}")
        return 1
    print(notes)
    return 0
