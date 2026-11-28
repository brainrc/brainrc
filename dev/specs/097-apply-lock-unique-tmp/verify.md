# Verify: Lock apply and use unique tmp names

Run at 2026-10-25T20:05:39Z on commit `fce02e4`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 378 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_aicfg.SyncFakeHomeTest.test_a_second_apply_fails_while_one_holds_the_lock` passes; manual: a separate process holds `apply.lock`, real `aicfg.py apply` → exit 1, `ERROR another aicfg apply is running (lock: …/apply.lock)`, `Nothing written.`, fresh HOME still empty | pass |
| AC2 | `test_the_lock_is_released_after_apply_even_on_error` passes (apply, apply raising, then flock succeeds and apply exits 0); manual: after the holder exits, apply → exit 0 | pass |
| AC3 | `test_temp_name_includes_the_pid` passes (`.settings.json.aicfg-tmp-<pid>`); `test_backups_are_capped` asserts no `.settings.json.aicfg-tmp*` left | pass |
| AC4 | `test_settings_changed_during_apply_are_left_alone` and `test_mcp.McpSyncTest.test_a_claude_json_changed_during_apply_is_left_alone` pass (exit 1, `CHANGED` line with "close Claude Code", file keeps the harness's write, other harness file still written) | pass |
| AC5 | `test_a_second_apply_fails_while_one_holds_the_lock` runs status while the lock is held → exit 0, "Dry run" | pass |
| AC6 | manual: docs/troubleshooting.md § "Apply while something else writes" says to close Claude Code before MCP changes and has a row for each message | pass |

## Notes
- Lock tests skip on Windows (`fcntl`); the `msvcrt` path is not exercised here.
- The AC2 test passes before the change too (no lock existed); it guards against a leaked lock.
- Manual run used a `git archive` copy of HEAD with scratch HOME and AICFG_HOME.
