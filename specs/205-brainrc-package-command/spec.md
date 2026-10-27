# Spec: Rename the PyPI package and the command to brainrc

Ticket: gh:205 (epic #199, 2 of 6) · Size: large · Status: draft

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
  the VERSION value and exits 0.
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
1. Should the `aicfg` import shim re-export `brainrc` submodules (`aicfg.cli`, `aicfg.hooks`...)
   or only `main`/`entry`? Default: alias `aicfg.cli` only, since the tests and the old script
   use that. *Matters for third-party imports.*
2. Should the deprecation warning be silenceable (env var)? Default: no, except Python's
   standard warning filters. *Pre-commit output noise.*
3. Does `--version` print bare `X.Y.Z` or `brainrc X.Y.Z`? Default: `brainrc X.Y.Z`. *Scripts
   that parse it.*
4. Wheel force-include targets move to `brainrc/_core/`; `AICFG_HOME` stays until #206.
   Default: confirm. *Installed users' hooks path must not break in between.*
5. PyPI: is the name `brainrc` reserved/owned? Default: assume yes; publishing is outside
   this ticket. *Install from PyPI fails otherwise.*
6. The shims warn for "one minor release": which version removes them? Default: next minor
   after this ships; stated in the warning text. *Callers need a date.*

## Proposed split
Build order; each child standard or smaller.

1. **Rename the Python package to brainrc, with import shim**: `git mv aicfg brainrc`; `aicfg/`
   becomes a shim package; `python -m brainrc`, `--version`, usage text names `brainrc`; tests
   updated. Criteria: AC6 (`-m` part), AC7, AC9, plus `--version` prints the version.
2. **Add brainrc script, console scripts, and distribution name**: `scripts/brainrc.py`;
   `scripts/aicfg.py` and `aicfg` console script warn and delegate; pyproject name `brainrc`,
   wheel packages and `_core` paths. Criteria: AC1, AC2, AC3, AC4, AC5, AC6 (`python -m aicfg`),
   AC8, AC11.
3. **Point CI and callers at brainrc**: `validate.yml`, `release.yml`, other in-repo invocations
   use `brainrc`/`scripts/brainrc.py`; a CI step proves the old names still work. Criteria: AC10.
