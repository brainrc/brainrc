# Verify: Hooks fail open when their file is missing

Run at 2026-10-25T23:17:04Z on commit `d316c8d`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 386 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands (plugin manifests current) |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `tests.test_hooks.FailOpenTest.test_claude_commands_pass_when_the_hooks_are_gone` passes; manual: fresh HOME, `apply`, moved `overrides/claude/hooks` away, ran the installed command via `sh -c` with a `git push` payload → exit 0, no output | pass |
| AC2 | `test_claude_commands_behave_like_the_guards_when_present` (exit and stdout equal the direct guard for a risky and a safe call; risky → `ask`); `test_cursor_commands_behave_like_the_guard_when_present` (→ `deny`); manual: installed command with hooks present → `permissionDecision: ask` | pass |
| AC3 | `test_cursor_commands_allow_when_the_hooks_are_gone` passes (exit 0, `{"permission": "allow"}`) | pass |
| AC4 | `tests.test_aicfg.DoctorTest.test_missing_hook_script` passes; manual: doctor after moving the hooks → `FAIL claude: hook missing: ~/.claude/hooks/ai-config/guard_outward.py` (and guard_secrets.py) | pass |
| AC5 | `test_broken_hook_script` passes (`exits 3`) | pass |
| AC6 | `test_every_hook_runs_with_an_empty_payload` (each guard run once with `{}` and timeout 5, no hook findings) and `test_clean_after_apply` pass | pass |
| AC7 | `test_apply_replaces_old_form_hook_groups` passes (old `python3 "…/guard_outward.py"` group replaced, no duplicate) | pass |

## Notes
- The AC7 test passes before the change too (ownership matching already replaced ai-config's groups); it guards the upgrade path.
- The manual "present" run printed the decision; zsh doesn't set `PIPESTATUS`, so its exit code wasn't captured. The AC2 tests compare exit codes.
- Doctor on the developer machine adds no hook findings. Its other FAILs come from a stale `~/projects/ai-config` install, which was already there.
