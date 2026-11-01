# Verify: Researcher role and proof report

Run at 2026-10-31T23:45:28Z on commit `ca6caaa`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: OK (1 skipped); tests/test_proof_guard.py 17 tests, tests/test_planning.py 6 tests |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | plan-report.md template (Candidates with proof and `path:line`), test_report_template_has_the_sections | pass (instruction text and template test) |
| AC2 | proof_guard.py run and matches (exit code plus normalized output; a timeout never matches); RunTest | pass (unit tests) |
| AC3 | planning.md: no proof or a failed re-verify goes under Needs evidence, never created | pass (instruction text) |
| AC8 | researcher.md never follows instructions from content; Flagged content taints the plan; ResearcherRoleTest | pass (instruction text and test) |
| AC9 | proof_guard.py scan (fails closed; proof output included), CheckTest secret, key and git-internal denials | pass (unit tests) |
| AC11 | Web only with `Web: on`; Sources not empty while off taints the plan | pass (instruction text; the harness cannot drop tools per dispatch) |
| AC12 | spikes on local `plan-<slug>/spike-<n>` branches, never pushed, and need an allowlisted command proof | pass (instruction text) |

## Notes
Security review: four rounds. The owner lifted the retry budget twice. The final review found no CRITICAL or HIGH; its MEDIUMs are fixed in ca6caaa. No real /plan run was performed (it needs a model).
