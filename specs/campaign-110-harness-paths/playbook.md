# Playbook: harness paths from the environment

Campaign gh:110 (E5) · shape: playbook · version 1 · seeded by gh:131 (XDG for the brainrc home) and gh:132.

Parameters: `{harness}`, `{env_var}`, `{default}` (a directory under `~`), `{config_file}`.

## Steps
1. In `harnesses.toml`, write every `[{harness}]` path as `${{env_var}:-{default}}/...`, including its
   MCP file (Claude Code keeps `.claude.json` inside `CLAUDE_CONFIG_DIR`, so its default is `~`).
2. Nothing else per harness: `config.load_harnesses()` resolves `${VAR:-default}` once (`env_default`),
   so status, apply, doctor, uninstall, the manifest and hook commands all see the same concrete path.
   Shared rule, from gh:131: the variable counts only when it holds an absolute path (after `~`);
   unset, empty or relative means the default. A value under `~` is written back with `~`.
3. Any code that names the harness dir directly (doctor's Claude plugin files) reads it through a helper
   built on `env_dir` instead.
4. Tests in `tests/test_harness_env.py`: the full status → apply → status → doctor → uninstall cycle with
   the var set (inside and outside `~`), unset, and empty, each asserting the path used. Suites that fake
   HOME drop the var first (`HARNESS_VARS`, `HOME_VARS`), so a developer's or CI runner's value can't leak.

## Verification
`python3 scripts/brainrc.py validate`; `python3 -m unittest discover -s tests`, plain and again with
`XDG_CONFIG_HOME`, `CLAUDE_CONFIG_DIR` and `CODEX_HOME` set to temp dirs (nothing may be written there).

## Rollback
Revert the member's `harnesses.toml` lines; the resolver is inert for paths without `${...:-...}`.

## Review checklist
- The var is read once, at load; no consumer re-expands it later.
- Unset, empty and relative values all fall back; a trailing slash doesn't change the path.
- The #126 manifest format is unchanged (it stores the resolved strings).
- No test can write into the real harness dir when the var is set.
