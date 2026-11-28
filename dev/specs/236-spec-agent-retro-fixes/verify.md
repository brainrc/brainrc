# Verify: spec-agent fixes from the rename campaign's retros

Run at 2026-10-29T02:14:13Z on commit `4175d8c`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (also with `XDG_CONFIG_HOME=/home/runner/.config`) | pass: 584 tests, OK (1 skipped) both ways |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | ReleaseTest `test_a_bump_into_the_shim_removal_release_fails_while_shims_remain` (failed before the change), `test_the_removal_check_is_off_once_the_shims_are_gone` | pass |
| AC2 | TempRepoCase pops and restores `XDG_CONFIG_HOME`; suite passes with it set | pass |
| AC3 | the three rules in SKILL.md § Auto mode, handoff.md § Dispatch prompt, agents/analyst.md | pass |
