# Plan: Rename the PyPI package and the command to brainrc

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none (stdlib only; hatchling stays build-time only).
- **Public API / contract changes:** distribution `ai-config` -> `brainrc`; new console script
  `brainrc`, `python -m brainrc`, `scripts/brainrc.py`, `--version`; import path `aicfg` -> `brainrc`.
  Deprecated: `aicfg` script, `scripts/aicfg.py`, `python -m aicfg`, `import aicfg` (aliases
  `aicfg.cli` only). Hint strings become `brainrc ...` / `python3 scripts/brainrc.py ...`.
  Affects pipx/uv users (reinstall as `brainrc`), packs' pre-commit hooks, CI callers.
- **Changelog:** `changelog.d/205-brainrc-package-command.md`, `bump: minor`, marked
  **[pack contract]**; ships as 0.4.0 and states the shims are removed in **0.5.0**.
- **Migrations / data changes:** none. Installed-mode hook paths move from `.../aicfg/_core/` to
  `.../brainrc/_core/`; the next `apply` rewrites them (existing behavior for a moved package).
- **Security triggers touched:** none. **Domains:** scripting, ci-pipelines.
- **Environments affected on deploy:** none (release workflow tags on merge; no PyPI publish, #200).
- **Destructive or replacing changes:** none.

## Approach
`git mv aicfg brainrc` so history follows the code, then fix self-references inside it:
`config.find_core`/`installed`/`command`, the `cli.py` usage docstring (written as
`brainrc.py ...`, rewritten to `brainrc ...` when `config.installed()`), and hint strings in
`sources.py`, `plugin.py`, `release.py`. `cli._dispatch` gains `--version`, printing
`brainrc {VERSION}` from the version `sources.core_version()` reads (works bundled and in a checkout).
pyproject ships both packages: `brainrc` (with `_core` force-included under `brainrc/_core`) and
the thin `aicfg` shim.

Deprecation lives in one place: `brainrc.cli.warn_deprecated(old)` prints one stderr line naming
`brainrc` and removal version `SHIM_REMOVED_IN = "0.5.0"`; `brainrc.cli.deprecated_entry` (the
`aicfg` console script), `scripts/aicfg.py`, and `aicfg/__main__.py` call it, then `main`. The
`aicfg/__init__.py` shim emits `DeprecationWarning` (Python filters; AC7) and puts
`sys.modules["aicfg.cli"] = brainrc.cli`. The CLI paths import `brainrc` directly, not `aicfg`,
so they show one warning, never two (AC11). Out of scope: `AICFG_HOME`, `aicfg_home()`, plugin
name `ai-config`, docs (#206-#209).

## Files
| File | Change |
|---|---|
| `aicfg/` -> `brainrc/` | `git mv` (a rename, not counted as changed lines); edit self-refs, `--version`, shim helpers |
| `aicfg/__init__.py`, `aicfg/__main__.py` | new: thin deprecated shim package |
| `scripts/brainrc.py` | new: checkout entry; `scripts/aicfg.py` becomes a warning shim |
| `pyproject.toml` | name, description, scripts, `packages = ["brainrc", "aicfg"]`, force-include targets |
| `tests/test_aicfg.py`, `tests/test_mcp.py`, `tests/test_hooks.py`, `scripts/evals.py` | import `brainrc`, patch targets `brainrc.*` |
| `tests/test_cli_entry_points.py` | new: deprecated-entry contract tests |
| `scripts/check_install.py` | new: post-install smoke check (stdlib, argv lists) run by CI |
| `.github/workflows/validate.yml`, `release.yml` | invoke `scripts/brainrc.py` / `brainrc`; run the smoke check |
| `changelog.d/205-brainrc-package-command.md` | new fragment |

## Risks
- `pip install brainrc` over an old `ai-config` install: both own an `aicfg` script. Fragment
  tells users to uninstall `ai-config` first.
- Tests keep `import brainrc as aicfg` so ~365 references in `test_aicfg.py` don't churn; only
  `mock.patch("aicfg.…")` strings and the import change.
- `SHIM_REMOVED_IN` is hardcoded; if another minor lands first, fix it at release review.

## Test strategy
Unit tests (`tests/test_aicfg.py`): `--version` output and exit code (AC1), usage names `brainrc`
and never `aicfg.py` in checkout and installed mode (AC9), `pyproject.toml` read with `tomllib`:
name, both scripts, packages, every force-include target under `brainrc/_core` and every source
present (AC2, AC8), `InstalledModeTest` on a `brainrc/_core` dir (AC8). Contract tests
(`tests/test_cli_entry_points.py`, subprocess with `sys.executable`): AC3 via `deprecated_entry`,
AC4, AC5, AC6 (`-m` on the checkout's `sys.path`), AC7, AC11 (stderr only, exactly once).
Built wheel / fresh install (AC1, AC2, AC3, AC6, AC7, AC8): **not provable offline here**:
hatchling isn't installed and pip can't fetch it, so neither a wheel build nor a temp-venv install
works. CI proves them: `validate.yml` runs `pip install .` (builds the wheel), then
`scripts/check_install.py` from `$RUNNER_TEMP` checks `importlib.metadata` dist name and entry
points, `brainrc --version`, `brainrc validate`, `aicfg status` vs `brainrc status`, `python -m`
both names, and `import aicfg`. PyPI is reachable from the run's container (engine checked: `pip download hatchling` works), so verify also builds the wheel and runs `scripts/check_install.py` from a temp venv locally; CI repeats it. Manual check with network:
`pip install . && cd /tmp && python3 <repo>/scripts/check_install.py`. actionlint/zizmor aren't
installed; YAML is checked by review.

## Tasks
- [ ] **T1** [agent: implementer] Rename the package to `brainrc` with `--version` and brainrc usage
  - files: `aicfg/*` -> `brainrc/*` (`git mv`; edits in `brainrc/__init__.py`, `__main__.py`, `cli.py`, `config.py`, `sources.py`, `plugin.py`, `release.py`), `scripts/brainrc.py`, `scripts/aicfg.py` (retarget import only), `scripts/evals.py`, `pyproject.toml`, `tests/test_aicfg.py`, `tests/test_mcp.py`, `tests/test_hooks.py`
  - criteria: AC1, AC2, AC4, AC8, AC9 (unit level); suite and `validate` green
  - review: each
- [ ] **T2** [agent: test-writer] Contract tests for the brainrc and deprecated aicfg entry points
  - files: `tests/test_cli_entry_points.py`
  - criteria: AC3, AC4, AC5, AC6, AC7, AC11
  - review: each
  - after: T1
- [ ] **T3** [agent: implementer] Deprecated `aicfg` shims to pass T2
  - files: `aicfg/__init__.py`, `aicfg/__main__.py`, `brainrc/cli.py`, `scripts/aicfg.py`, `pyproject.toml`
  - criteria: AC3, AC5, AC6, AC7, AC11
  - review: each
  - after: T2
- [ ] **T4** [agent: implementer] CI invokes brainrc and smoke-tests the installed wheel
  - files: `scripts/check_install.py`, `.github/workflows/validate.yml`, `.github/workflows/release.yml`
  - criteria: AC10; AC1-AC3, AC6-AC8 on a fresh install (verify after push: validate)
  - review: each
  - after: T3
- [ ] **T5** [agent: implementer] Changelog fragment, `bump: minor`, **[pack contract]**, removal in 0.5.0
  - files: `changelog.d/205-brainrc-package-command.md`
  - criteria: AC10 (`validate` accepts the fragment)
