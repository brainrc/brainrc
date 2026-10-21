# Verify: Record the active run's path for external tools

Run at 2026-10-21T01:42:06Z on commit `142747e`. Raw logs in `specs/071-active-run-pointer/.runs/`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 234 passed, 0 failed (exit 0; `.runs/test.log`) |
| Targeted verbose | `python3 -m unittest discover -s tests -p test_active_run.py -v` | pass: 17 passed, 0 failed (`.runs/test-active-run-verbose.log`) |
| Lint | none configured | not configured |
| Build | none configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: `OK: 26 skills, 9 agents, 0 commands` (`.runs/validate.log`) |
| Plan / diff | n/a | offline only |
| AC1 scenario (manual) | see Notes, item 1 | pass (`.runs/ac1-cli.log`) |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_write_from_other_directory_records_absolute_run_path` passes. Manual: run dir in `.runs/ac1/repo-a/specs/071-x`, `write` from `.runs/ac1/session-b`, `read` from `.runs/ac1/cwd-c` printed `/home/user/ai-config/specs/071-active-run-pointer/.runs/ac1/repo-a/specs/071-x` (exit 0); pointer bytes end in `\n` | pass |
| AC2 | `test_write_defaults_to_dot_config_ai_config_when_env_unset` passes (HOME temp, AICFG_HOME unset) | pass |
| AC3 | `test_pointer_is_single_line_path_plus_newline_only` passes (byte-exact `path\n`); manual `od -c` of AC1 pointer shows one path and one `\n` | pass |
| AC4 | Doc: `references/lifecycle.md:36-37` (intake step 5 runs `active_run.py write`); `SKILL.md:74-75` (run once the run exists, after intake). Agent behavior, not executable here | pass |
| AC5 | Script: `test_write_replaces_another_runs_pointer` passes. Doc: resume step 1 at `references/state.md:134-135`; `SKILL.md:71-75` | pass |
| AC6 | Doc: `references/state.md:125-126` (write at every checkpoint commit: each gate, block, done); `SKILL.md:84` ("Run ... with every checkpoint commit"; checkpoint on blocked and done) | pass |
| AC7 | Doc: `references/state.md:127` ("Never cleared at done or abandon"). Script: `active_run.py` has only `write` and `read` subcommands, no clear path | pass |
| AC8 | `test_write_creates_missing_aicfg_home_directory` passes (parent `cfg/` absent before write) | pass |
| AC9 | `test_read_prints_pointer_run_when_directory_exists` passes; both `write` and `read` subcommands exercised in the AC1 manual run | pass |
| AC10 | `test_read_without_pointer_returns_newest_run_in_cwd_specs`, `test_read_with_pointer_to_missing_directory_falls_back_to_cwd_specs`, `test_read_fallback_orders_by_state_json_mtime_not_name`, `test_read_with_blank_pointer_falls_back_to_cwd_specs`, `test_read_with_pointer_naming_a_file_falls_back_to_cwd_specs` pass | pass |
| AC11 | `test_write_warns_and_exits_zero_when_aicfg_home_is_a_file` and `test_write_warns_and_exits_zero_when_default_home_is_unwritable` pass (rc 0, `WARN` on stderr, empty stdout) | pass |
| AC12 | Doc: `references/state.md:121-129` covers location (L123-124), format (L123-124), write moments (L125-126), persistence and last-write-wins (L127), fallback to `<cwd>/specs/` (L129) | pass |

## Notes
1. Manual AC1 run used `HOME` and `AICFG_HOME` set to temp dirs under `specs/071-active-run-pointer/.runs/ac1/`; the real `~/.config` was not touched.
2. No flaky failures observed; the suite ran once, green. No tests skipped.
3. AC4-AC7 and the resume/checkpoint write moments are agent-orchestration behavior; they are verified by documentation citation only, as the spec states. The orchestration mod is out of scope.
4. Working tree was clean before verify (`git status --short` empty at commit `142747e`).
