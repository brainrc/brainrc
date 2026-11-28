# Spec: Rename the PyPI package and the command to brainrc

Ticket: gh:205 (epic #199, 2 of 6) · Size: standard · Status: approved

## Problem
Users should install and type `brainrc`, but the distribution is `ai-config`, the command and
Python package are `aicfg`, and usage text says `aicfg.py`. Existing callers (packs' pre-commit
hooks run `~/ai-config/scripts/aicfg.py`, CI runs `aicfg`) must keep working for one minor
release, with a deprecation warning. There is no `--version` flag today.

## Goals
- `brainrc` is the distribution, console script, import package, `python -m` target, and the
  name in help/usage text.
- `aicfg` console script, `scripts/aicfg.py`, and `import aicfg` keep working and warn.

## Non-goals
- Settings home `~/.config/brainrc` / `BRAINRC_HOME` (#206); owned hooks dir, MCP ownership,
  backups (#207); plugin namespace `brainrc@brainrc` (#208); docs/wording pass (#209).
- Removing the `aicfg` shims (a later minor release).
- Renaming `specs/living/aicfg-*.md` files or the `AICFG_HOME` variable.

## Acceptance criteria
- **AC1**: Given a fresh install of the built wheel, when `brainrc --version` runs, then it prints
  `brainrc <VERSION>` (no `v` prefix, e.g. `brainrc 0.3.50`) on stdout and exits 0.
- **AC2**: Given the wheel metadata, then the distribution name is `brainrc` and the console
  scripts are `brainrc` and `aicfg`.
- **AC3**: Given a fresh install, when `aicfg status` runs, then stderr has a deprecation warning
  naming `brainrc`, and stdout and exit code equal those of `brainrc status`.
- **AC4**: Given a checkout, when `python3 scripts/brainrc.py validate` runs, then it behaves as
  `brainrc validate` with no warning.
- **AC5**: Given a checkout, when `python3 scripts/aicfg.py validate --pack .` runs, then it
  warns on stderr and gives the same stdout and exit code as `scripts/brainrc.py`.
- **AC6**: Given an install, when `python -m brainrc status` runs, then it works; `python -m aicfg
  status` works and warns.
- **AC7**: Given an install, when `import aicfg` runs, then it emits a `DeprecationWarning` and
  `aicfg.cli.main` still resolves.
- **AC8**: Given the wheel, when installed, then bundled core data (skills, agents, rules,
  `harnesses.toml`, VERSION, CHANGELOG) is found under the `brainrc` package and
  `brainrc validate` passes from outside a checkout.
- **AC9**: Given `brainrc` with no command or an invalid one, then usage text names `brainrc`
  (never `aicfg.py`).
- **AC10**: Given the repo, when the test suite, `validate`, and both CI workflows' commands run,
  then all pass, with workflows invoking `brainrc`/`scripts/brainrc.py`.
- **AC11**: Given the deprecated entry points, then the warning appears once per invocation and
  never on stdout.

## Constraints
- Stdlib-only Python 3.11+; hatchling build-time only. Offline validation only.
- `dist/`, `.claude-plugin/`, `.cursor-plugin/`, root `plugin.json` are generated, not hand-edited.
- Behavior of all commands is otherwise unchanged.

## Requirement changes
### Area: cli-entry-points
Purpose: How the tool is installed and invoked, and how deprecated names behave.
#### ADDED: brainrc command
The system SHALL install as distribution `brainrc` with console script `brainrc`, import package
`brainrc`, `python -m brainrc`, `scripts/brainrc.py`, and `--version`, with usage text naming
`brainrc`. (AC1, AC2, AC4, AC6, AC8, AC9)
#### ADDED: Deprecated aicfg names
The system SHALL keep the `aicfg` console script, `scripts/aicfg.py`, `python -m aicfg`, and
`import aicfg` working through one minor release, each warning (on stderr / as a
`DeprecationWarning`) and otherwise behaving as `brainrc`. (AC3, AC5, AC6, AC7, AC11)

Existing living requirements mention `aicfg` commands by name; their wording is left to #209.

## Open questions
Resolved at the Spec gate:
1. Import shim: alias `aicfg.cli` only (default).
2. Warning is not silenceable beyond Python's standard warning filters (owner).
3. `--version` prints `brainrc X.Y.Z`, no `v` prefix (owner chose `brainrc`; engine recommended no `v`, matching VERSION, PEP 440, and uv/pip; tags keep `v`).
4. Bundled data moves to `brainrc/_core/`; `AICFG_HOME` stays until #206 (default).
5. PyPI publishing is out of scope; the name is not yet reserved (#200) (default).
6. Shims are removed in the minor after the one this ships in; the warning names that version (owner). This change bumps `minor`.

## Proposed split
Not applicable: resized to standard by the owner; built as one ticket.
