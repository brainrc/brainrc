# Verify: Readable config errors

Run at 2026-10-27T02:23:50Z on commit `89e3bc7`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 409 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `ConfigErrorTest.test_toml_syntax_error_names_file_and_line`, `test_toml_syntax_error_at_end_of_document`, `test_syntax_error_in_shipped_file`, `test_pack_toml_syntax_error_names_file_and_line` pass (status, apply, validate exit 1 with `ERROR <file>:<line>: invalid TOML`, nothing in HOME, doctor FAIL + exit 1); manual: `skills = ` on line 3 → `apply` prints `ERROR …/harnesses.local.toml:3: invalid TOML: Invalid value`, exit 1, no traceback | pass |
| AC2 | `test_top_level_value_needs_a_table` passes; manual: `claude = false` on line 2 → `status` exit 1 with `` `claude` must be a table, e.g. [claude] ``; doctor FAIL with the same text | pass |
| AC3 | `test_enabled_must_be_a_boolean`, `test_pack_enabled_must_be_a_boolean`, `test_path_keys_must_be_strings`, `test_inline_table_value_points_at_its_line` pass; manual: `enabled = "false"` → `validate` exit 1, `[codex] `enabled` must be true or false` | pass |
| AC4 | `test_unknown_harness_key_warns`, `test_unknown_pack_key_warns` pass (one WARN per command, exit 0, doctor WARN); manual: `enabeld` → `WARN …:2: unknown key `enabeld` in [claude]` in status and doctor | pass |
| AC5 | `test_harness_only_in_local_file_warns_and_still_loads` passes (warning, and `[cursr]` skills still linked); manual: `WARN …:3: unknown harness [cursr]` | pass |
| AC6 | `test_pack_name_and_prefix_must_be_strings` passes (`name = 7`, `prefix = false` → ERROR with pack.toml path and line 2) | pass |
| AC7 | `ClosedStdoutTest.test_closed_stdout_exits_without_a_traceback` passes (doctor and status with a closed stdout: exit 0, no traceback); manual: `doctor | head -c 10` → empty stderr | pass |
| AC8 | `test_shipped_config_is_quiet` passes; manual: real checkout `validate` OK and `status` prints 0 WARN lines | pass |

## Notes
- Manual runs used a `git archive` copy of HEAD with a scratch HOME and AICFG_HOME; nothing real was touched.
- On a config error, `apply` still creates `$AICFG_HOME/apply.lock` (the lock from gh:97 is taken before any config is read); no harness file is written.
- Review ran in the same session (`review_context: shared`).
