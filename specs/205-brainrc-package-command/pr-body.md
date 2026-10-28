Rename the package and command to brainrc

## Why
Users should install and run `brainrc`. The distribution was `ai-config`, and the command and
Python package were `aicfg`. Existing callers (packs' pre-commit hooks, CI) must keep working for
one minor release, so the old names stay with a deprecation warning.

## What changed
- The tool is `brainrc` everywhere a user types or imports it: the PyPI distribution, the
  `brainrc` command, `import brainrc`, `python -m brainrc`, `scripts/brainrc.py`, and the usage text.
- `brainrc --version` prints `brainrc <VERSION>` (new, since there was no version flag).
- **[pack contract]** The old names keep working through 0.5.0: the `aicfg` command,
  `scripts/aicfg.py`, `python -m aicfg`, and `import aicfg`. Each prints one deprecation line on
  stderr that names `brainrc`. Stdout and exit codes match `brainrc`. Packs' pre-commit hooks should
  point at `scripts/brainrc.py` before 0.5.0.
- Installed users run `uv tool uninstall ai-config` (or `pipx uninstall ai-config`) before
  installing `brainrc`. Both ship an `aicfg` command, and removing `ai-config` afterwards deletes
  the new one. The changelog fragment and `docs/install.md` say so.
- Installed hook paths move from `.../aicfg/_core/` to `.../brainrc/_core/`. The next `brainrc apply`
  rewrites them.
- CI (`validate.yml`, `release.yml`) runs `brainrc`. `scripts/check_install.py` smoke-tests the
  installed wheel.
- Other command behavior is unchanged. `AICFG_HOME`, `~/.config/ai-config`, and the plugin name are
  unchanged here (#206 to #208).

## Acceptance criteria
- [x] AC1: `brainrc --version` prints `brainrc 0.3.50`, exit 0, verified by `check_install.py` (AC1) and the `--version` unit test
- [x] AC2: distribution `brainrc`, scripts `brainrc` and `aicfg`, verified by `check_install.py` (AC2) and the pyproject `tomllib` test
- [x] AC3: `aicfg status` warns on stderr, and stdout and exit match `brainrc status`, verified by `check_install.py` (AC3) and `tests/test_cli_entry_points.py`
- [x] AC4: `scripts/brainrc.py validate` has no warning, verified by `test_ac4_scripts_brainrc_validate_has_no_warning`
- [x] AC5: `scripts/aicfg.py validate --pack .` warns once and matches `scripts/brainrc.py`, verified by `test_ac5_*`
- [x] AC6: `python -m brainrc` and `python -m aicfg` work, and only `aicfg` warns, verified by `check_install.py` (AC6) and `test_ac6_*`
- [x] AC7: `import aicfg` emits `DeprecationWarning`, and `aicfg.cli.main` resolves, verified by `check_install.py` (AC7) and `test_ac7_*`
- [x] AC8: bundled `_core` is found under `brainrc`, and `brainrc validate` passes outside a checkout, verified by `check_install.py` (AC8)
- [x] AC9: usage names `brainrc`, never `aicfg.py`, verified by `test_usage_names_brainrc_*`
- [x] AC10: suite, `validate`, and the workflow commands pass locally, and the `validate` workflow (including `check_install.py` on the runner) passed on this PR
- [x] AC11: each deprecated entry warns once, on stderr only, verified by `test_ac11_*`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
python3 -m venv "$HOME/brainrc-venv"
"$HOME/brainrc-venv/bin/pip" install <repo>
brainrc_bin="$HOME/brainrc-venv/bin"
cd "$(mktemp -d)" && PATH="$brainrc_bin:$PATH" "$brainrc_bin/python" <repo>/scripts/check_install.py
```
`check_install.py` prints one PASS or FAIL line per check. It exits 2 if `brainrc` is not the
installed copy (for example, when run from inside the checkout).

## Follow-ups
- `docs/architecture.md` and `AGENTS.md` still describe the `aicfg/` package (#209).
- Pre-existing: the `scripts/brainrc.py` docstring says "run with no command for usage" and does
  not match the CLI (no command runs `status`). Not changed here.
- Remove the deprecated `aicfg` CI step and the shims in 0.5.0.
- `check_install.py` refuses a `pip install --user` install, because its scripts sit outside the
  interpreter's scripts dir. CI uses a normal install.

2 of 6 in epic #199 (rename to brainrc), after #229

Spec: `specs/205-brainrc-package-command/spec.md` · Plan: `specs/205-brainrc-package-command/plan.md`
Closes #205

🤖 Generated with [Claude Code](https://claude.com/claude-code)
