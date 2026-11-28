# Verify: Refetch a git pack when its ref or URL changes

Run at 2026-10-27T02:42:56Z on commit `4b294b3`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 424 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only (local bare repos) |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `GitPackTest.test_apply_follows_a_ref_change` passes; manual: `ref` v1 → v2, apply prints `FETCH … (v2)` and `CREATE claude ~/.claude/skills/acme-new` | pass |
| AC2 | same test: `status` prints `FETCH … (v2)`, clone has no `skills/acme-new`; manual: status prints the FETCH line | pass |
| AC3 | `test_apply_follows_a_url_change` passes (old bare repo removed, fetched from the new URL) | pass |
| AC4 | `test_doctor_flags_a_clone_that_doesnt_match` passes; manual: `FAIL pack acme: fetched ref \`v1\`, packs.toml says \`v2\``, fix `… apply fetches it` | pass |
| AC5 | `test_unchanged_config_does_not_fetch` passes (no FETCH, `subprocess.run` not called); manual: a second apply prints 0 FETCH lines | pass |
| AC6 | `test_a_hung_git_call_times_out` (ERROR `git init timed out after 60s`, Nothing written, no clone, empty HOME) and `test_git_calls_have_a_timeout` (every call has `timeout=60`) pass | pass |
| AC7 | `test_a_clone_without_a_record_is_fetched_once` passes (status FETCH, apply records, then no FETCH) | pass |

## Notes
- Review ran in the same session (`review_context: shared`); security checklist applied to the git calls, no findings.
- AC6 is tested with a mocked timeout, not a real 60s hang.
