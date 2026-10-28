"""The old names `aicfg` and `ai-config` appear only where ALLOW says they may.

Every tracked or untracked-not-ignored file is scanned, except CHANGELOG.md, changelog.d/ and
specs/. For each line, the allowed matches are deleted; what still contains an old name fails.
An ALLOW row that matches no line fails too, so the table cannot go stale.
"""
import fnmatch
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = ("CHANGELOG.md", "changelog.d/", "specs/")
OLD = re.compile(r"(?i)aicfg|ai-config")
MAX_SHOWN = 50

# A line that says the name is old, so a docs sentence may still mention it (category E).
OLD_LINE = r"^(?=.*(?i:\bold\b|former|deprecated|legacy)).*$"

# (path glob, regex, reason). Globs use fnmatch: `*` also crosses `/`.
ALLOW = [
    # A. Shim files and tests that exercise old names, whole file.
    ("aicfg/*", r".*", "A: the aicfg shim package"),
    ("scripts/aicfg.py", r".*", "A: the deprecated script"),
    ("scripts/check_install.py", r".*", "A: the old install checker shim"),
    ("tests/test_cli_entry_points.py", r".*", "A: tests the old entry points"),
    ("tests/test_settings_home.py", r".*", "A: tests the old settings home"),
    ("tests/test_migrate.py", r".*", "A: tests migrate from the old home"),
    ("tests/test_doctor_home.py", r".*", "A: tests the old-home doctor warning"),
    ("tests/test_doctor_plugin.py", r".*", "A: tests the old-plugin doctor warning"),
    ("tests/test_rename_converge.py", r".*", "A: tests old and new names converge"),
    ("tests/test_ownership.py", r".*", "A: tests ownership of old hook dirs"),
    ("tests/test_backups.py", r".*", "A: tests old backup names"),
    ("tests/test_plugin_docs.py", r".*", "A: checks docs for the old plugin name"),
    ("tests/test_active_run.py", r".*", "A: tests the old-home fallback"),
    # A, partly: tests that keep a few exact legacy tokens.
    ("tests/test_brainrc.py", r"AICFG_HOME", "A: the deprecated env var"),
    ("tests/test_brainrc.py", r"\.config\W+ai-config", "A: the legacy settings home"),
    ("tests/test_brainrc.py", r"ai-config-guard\.js", "A: D's OpenCode link name"),
    ("tests/test_brainrc.py", r'assertNotIn\("ai-config", text, rel\)', "A: no manifest names the old plugin"),
    ("tests/test_brainrc.py", r"""replace\('"brainrc"', '"ai-config"', 1\)""", "A: seeds a stale old-name manifest"),
    ("tests/test_brainrc.py", r'hooks / "ai-config(-acme)?(/mine\.py)?"', "A: seeds old hook dirs"),
    ("tests/test_brainrc.py", r'for d in \("ai-config", "ai-config-acme"\)', "A: old hook dir names"),
    ("tests/test_brainrc.py", r'\["ai-config", "ai-config-acme", "mine"', "A: old hook dir names"),
    ("tests/test_brainrc.py", r"aicfg-fetched\.json", "A: the fetch record name, kept"),
    ("tests/test_brainrc.py", r"def test_aicfg_home_is_a_deprecated_alias", "A: the alias test"),
    ("tests/test_brainrc.py", r"brainrc(\.config)?\.aicfg_home", "A: the deprecated alias"),
    ("tests/test_brainrc.py", r"shadows the aicfg package", "A: why the alias test uses a subprocess"),
    ("tests/test_brainrc.py", r"import aicfg\.cli.*aicfg\.cli\.aicfg_home", "A: the alias via the shim"),
    ("tests/test_brainrc.py", r'assertNotIn\("aicfg(\.py)?", ', "A: usage text names no old script"),
    ("tests/test_brainrc.py", r'assertIn\("aicfg", scripts\)', "A: the aicfg console script"),
    ("tests/test_brainrc.py", r"hooks/ai-config", "A: old hook dirs"),
    ("tests/test_brainrc.py", r"scripts/aicfg\.py", "A: the deprecated script"),
    ("tests/test_hooks.py", r"hooks/ai-config", "A: old hook dirs"),
    ("tests/test_hooks.py", r'"ai-config"', "A: the old hook dir name"),
    ("tests/test_mcp.py", r'"ai-config"', "A: the legacy settings home"),
    # B. Packaging.
    ("pyproject.toml", r'^aicfg = "brainrc\.cli:deprecated_entry"', "B: the aicfg console script"),
    ("pyproject.toml", r'"aicfg"', "B: the aicfg shim package"),
    (".github/workflows/validate.yml", r"deprecated aicfg script", "B: CI step name"),
    (".github/workflows/validate.yml", r"scripts/aicfg\.py", "B: CI runs the deprecated script"),
    # C. Old-install detection or migration in code.
    ("brainrc/config.py", r"AICFG_HOME", "C: resolves the deprecated env var"),
    ("brainrc/cli.py", r"AICFG_HOME", "C: usage text and the deprecated-home warning"),
    ("brainrc/doctor.py", r"AICFG_HOME", "C: warns about the deprecated env var"),
    ("brainrc/migrate.py", r"AICFG_HOME", "C: migrates from the deprecated env var home"),
    ("skills/spec-agent/scripts/active_run.py", r"AICFG_HOME", "C: the deprecated env var"),
    ("brainrc/config.py", r"\.config/ai-config", "C: the legacy settings home, in a docstring"),
    ("brainrc/cli.py", r"\.config/ai-config", "C: the legacy settings home, in usage text"),
    ("brainrc/migrate.py", r"\.config/ai-config", "C: the legacy settings home, in the docstring"),
    ("skills/spec-agent/scripts/active_run.py", r"\.config/ai-config", "C: the legacy settings home"),
    ("brainrc/config.py", r'"ai-config"', "C: the legacy dir and old hook dir as path parts"),
    ("brainrc/doctor.py", r'"ai-config"', "C: the old Cursor plugin link as a path part"),
    ("skills/spec-agent/scripts/active_run.py", r'"ai-config"', "C: the legacy dir as a path part"),
    ("brainrc/config.py", r"\(\?:ai-config\|brainrc\)", "C: OWNED_HOOK matches old hook dirs"),
    ("brainrc/config.py", r"former ai-config", "C: comment on OWNED_HOOK"),
    ("brainrc/settings.py", r"bak-\(\?:brainrc\|aicfg\)", "C: old backup names"),
    ("brainrc/doctor.py", r"ai-config@ai-config", "C: the old plugin id"),
    ("brainrc/doctor.py", r"marketplace remove ai-config", "C: old plugin removal hint"),
    ("brainrc/doctor.py", r"old ai-config plugin", "C: old Cursor plugin warning"),
    ("brainrc/__init__.py", r"\baicfg_home\b", "C: deprecated alias, kept until 0.5.0"),
    ("brainrc/config.py", r"\baicfg_home\b", "C: deprecated alias, kept until 0.5.0"),
    ("brainrc/cli.py", r'warn_deprecated\("aicfg"\)', "C: the deprecation line"),
    ("brainrc/cli.py", r"aicfg_home,  # noqa: F401  deprecated alias, kept so aicfg\.cli\.aicfg_home",
     "C: the deprecated alias import"),
    ("brainrc/cli.py", r"The deprecated `aicfg` console script", "C: docstring of the shim entry"),
    ("brainrc/doctor.py", r"when the old `ai-config` plugin", "C: docstring of the old-plugin check"),
    # D. On-disk names kept for compatibility.
    ("brainrc/mcp.py", r"# >>> ai-config mcp servers \(written by aicfg apply; edits here are replaced\)",
     "D: Codex block start marker"),
    ("brainrc/mcp.py", r"# <<< ai-config mcp servers", "D: Codex block end marker"),
    ("harnesses.toml", r"ai-config-guard\.js", "D: OpenCode plugin link"),
    ("brainrc/packs.py", r"\.git/aicfg-fetched\.json", "D: the fetch record"),
    # E. Docs sentences about old names: exact tokens, or lines that say old/former/deprecated/legacy.
    ("docs/install.md", OLD_LINE, "E: upgrade and old-name notes"),
    ("docs/install.md", r"uv tool uninstall ai-config|pipx uninstall ai-config", "E: upgrade step"),
    ("docs/install.md", r"Moving from ai-config", "E: the migration section heading"),
    ("docs/install.md", r"ai-config@ai-config|marketplace remove ai-config", "E: old plugin removal"),
    ("docs/install.md", r"plugins/local/ai-config", "E: old Cursor link"),
    ("docs/troubleshooting.md", OLD_LINE, "E: old-plugin and AICFG_HOME entries"),
    ("docs/troubleshooting.md", r"moving-from-ai-config|Moving from ai-config", "E: link to the migration section"),
    ("docs/troubleshooting.md", r"AICFG_HOME|ai-config@ai-config", "E: old env var and plugin id"),
    ("docs/troubleshooting.md", r"bak-aicfg", "E: old backup names"),
    ("skills/spec-agent/SKILL.md", OLD_LINE, "E: old-name fallbacks"),
    ("skills/spec-agent/SKILL.md", r"before `brainrc migrate`: `~/\.config/ai-config/`", "E: the pre-migrate home"),
    ("skills/spec-agent/SKILL.md", r"ai-config:<role>", "E: old role names, checked by test_plugin_docs"),
    ("skills/spec-agent/references/state.md", r"\.config/ai-config", "E: legacy settings home"),
    # F. The allowlist test itself.
    ("tests/test_old_names.py", r".*", "F: this table"),
]


def repo_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return sorted(p for p in set(out) if not p.startswith(SKIP))


def scan() -> tuple[list[str], list[str]]:
    """(offending "path:line: text" entries, ALLOW rows that matched nothing)."""
    rows = [(g, re.compile(rx), why) for g, rx, why in ALLOW]
    used = [False] * len(rows)
    offenders = []
    for rel in repo_files():
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        fitting = [i for i, (g, _, _) in enumerate(rows) if fnmatch.fnmatchcase(rel, g)]
        for n, line in enumerate(lines, 1):
            if not OLD.search(line):
                continue
            rest = line
            for i in fitting:
                if rows[i][1].search(line):
                    used[i] = True
                    rest = rows[i][1].sub("", rest)
            if OLD.search(rest):
                offenders.append(f"{rel}:{n}: {line.strip()[:120]}")
    stale = [f"{g} /{rx.pattern}/ ({why})" for (g, rx, why), u in zip(rows, used) if not u]
    return offenders, stale


class OldNamesTest(unittest.TestCase):
    def test_only_allowlisted_old_names_remain(self):
        offenders, stale = scan()
        problems = []
        if offenders:
            shown = offenders[:MAX_SHOWN]
            more = len(offenders) - len(shown)
            problems.append(f"{len(offenders)} line(s) name aicfg/ai-config outside ALLOW:\n  "
                            + "\n  ".join(shown) + (f"\n  ... and {more} more" if more else ""))
        if stale:
            problems.append(f"{len(stale)} ALLOW row(s) match no line (stale):\n  " + "\n  ".join(stale))
        if problems:
            self.fail("\n".join(problems))


if __name__ == "__main__":
    unittest.main()
