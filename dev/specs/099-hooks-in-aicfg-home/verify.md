# Verify: Copy hooks into AICFG_HOME

Run at 2026-10-25T23:45:41Z on commit `214add7`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 392 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `tests.test_aicfg.InstalledModeTest.test_installed_hooks_link_into_a_copy_in_aicfg_home` passes; manual: `pip install` into a Python 3.12 venv, `aicfg apply` → `~/.claude/hooks/ai-config` → `$AICFG_HOME/hooks/core/claude/hooks` | pass |
| AC2 | `test_guards_still_run_after_the_package_is_gone` passes; manual: reinstalled on 3.13, deleted the 3.12 venv, no re-apply → installed Claude command `ask`, Cursor command `deny` for `git push origin main`; doctor has no hook findings | pass |
| AC3 | `test_an_upgraded_package_refreshes_the_copy` passes (status `UPDATE`, copy matches, leftover file gone, then in sync) | pass |
| AC4 | `SyncFakeHomeTest.test_checkout_hooks_link_into_the_checkout` passes | pass |
| AC5 | `test_an_old_link_into_the_package_is_repointed` passes (`UPDATE`, re-pointed, doctor clean) | pass |
| AC6 | `test_disabling_every_hooked_harness_removes_the_copy` passes (cursor link pruned and copy kept; then both disabled → `PRUNE` and copy removed) | pass |

## Notes
- The real upgrade run used pip venvs (3.12, then 3.13), not `uv tool upgrade`, because uv isn't installed here and the pipx shim fails under a scratch HOME. The mechanism is the same: a new Python means a new site-packages path.
- That run also found an older problem outside this ticket: after a Python change, skill and agent links into the old venv show as 140 `CONFLICT`s, and `apply` doesn't re-link them. install.md now says so (F1). Follow-up: treat a dangling link into an old `_core` as `update`.
- The AC4 test passes before the change too; it guards checkout behavior.
