# Plan: install aicfg with pipx or uv, no clone

**New build-time dependency:** `hatchling` (declared in `pyproject.toml`, fetched by pip or uv when
building; not imported at runtime). Reason: declarative bundling of repo-root content into the
wheel (`force-include`), no `setup.py`. No public API change.

A prototype wheel built with `uv build` (94 files): `aicfg/` plus `aicfg/_core/{skills,agents,
rules,overrides,mcp}` and the TOML/VERSION/CHANGELOG files. No `*.local.*` or caches. The `roles`
symlink becomes real copies of the agent files.

## Approach
- `config`: `REPO` is `aicfg/_core` when it exists, else the checkout; `installed()` says which.
  `local_dir()` is `$AICFG_HOME` when installed, else the repo. `_layered` reads
  `<name>.local.toml` from `local_dir()`.
- `sources.render_instructions`: core's `*.local.md` rules come from `local_dir()/rules`.
- `cli.cmd_sync`: when installed, skip the deprecated in-repo `extensions.md` and the legacy
  `dist/` cleanup. `doctor` skips the in-repo `extensions.md` check the same way.
- `plugin`: when installed, `cmd_plugin` prints an error (run it from a checkout) and exits 1;
  `check_plugin` has nothing to check (no `.claude-plugin/` in `_core`).
- `validate.check_roles_link`: when installed, `roles/` holding copies is expected.
- `cli.entry()` for the console script.

## Tasks
| id | title | agent | files | criteria |
|---|---|---|---|---|
| T1 | tests first: detection, local files, no writes in the package, roles | implementer | tests/test_aicfg.py | AC2, AC3, AC5 |
| T2 | aicfg changes | implementer | aicfg/{config,sources,cli,doctor,plugin,validate}.py | AC2, AC3 |
| T3 | `pyproject.toml`; CI builds and runs the installed `aicfg validate` | implementer | pyproject.toml, .github/workflows/validate.yml | AC1, AC5 |
| T4 | real `uv tool install` in a fake HOME, compared with a checkout | implementer | none | AC4 |
| T5 | docs and release | implementer | README.md, docs/harness-packages.md, CHANGELOG.md, VERSION | AC6 |
