# Verify: Campaign ordered-shape fixes from gh:77

Run at 2026-10-25T02:17:19Z on commit `33b172b`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 367 passed, 0 failed |
| Lint | — | not configured |
| Build | — | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: 26 skills, 9 agents, 0 commands |
| Plan / diff | — | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | campaign.md:152 Retarget rule: merge `main`, re-run tests, retarget base to `main`; "A child PR merges only with base `main`" | pass |
| AC2 | campaign.md:148-150: stacked body "N of M, stacked on #X. Retarget to `main` before merging." | pass |
| AC3 | campaign.md:144-150: Deliver gate asks `sequential` (default) or `stacked`, recorded as `delivery`; schema line 113 | pass |
| AC4 | campaign.md:28 and :122 status `verified`; :169 resume skips verified, all-verified presents Deliver gate; state.md:163-165 | pass |
| AC5 | campaign.md:126-132 § State home: child branch in progress, own entry only while building, stack tip from Deliver gate on | pass |
| AC6 | agents/architect.md:28-30 linked tasks get `after:`, never share a wave; efficiency.md wave rule | pass |
| AC7 | `python3 -m unittest tests.test_worktree_fence -v` → 7 ok (pass, tracked stray, untracked stray, rename source, main write, allow prefix, git error) | pass |
| AC8 | efficiency.md:44-49 fence before landing, `git -C <worktree>` for all worktree git; handoff.md:56 | pass |
| AC9 | `python3 -m unittest -v tests.test_evals.CampaignCheckTest` → stacked pass, retargeted pass, merged-into-stacked-base fail, bad base fail, no PR fail, unknown delivery fail; sequential tests unchanged and passing | pass |
| AC10 | skills/spec-agent/SKILL.md:158-160 engine edits after approval: wording/path only, logged, listed at Deliver gate | pass |

## Notes
Doc criteria checked by reading the cited lines. Review ran in a fresh-context subagent (`review_context: fresh`). No ordered campaign has run with these rules yet.
