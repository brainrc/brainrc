# Verify: spec-agent `--auto` mode, no gate stops, draft PR(s) as output

Run at 2026-10-27T03:37:24Z on commit `2313d50`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 438 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | SKILL.md § Auto mode: `auto: true` "from the flag itself, never from reply wording"; § Run 4 keeps the self-approval rule, "only the `--auto` flag at the start of a run changes this"; state.md `auto` row; work/SKILL.md "no wording of mine means `--auto`". `AutoCaseTest.test_a_run_without_the_flag_or_with_a_stop_fails` (auto false fails) | pass |
| AC2 | live sandbox run of ticket 011 with the new rules: `evals.py check <sandbox> evals/cases/sandbox-008.toml` → 17 passed, 0 failed (gates logged `auto-approved`, both timestamps, branch as PR, main untouched). sandbox-009 (standard) graded on a synthetic run by `AutoCaseTest` | pass |
| AC3 | templates/pr-body.md `## Decisions made without you`; SKILL.md § Auto mode lists defaults and security triggers there; live run's pr-body.md has it (sandbox-008 check) | pass |
| AC4 | guardrails.md Auto mode rows + SKILL.md § Auto mode hard stops; live sandbox run of ticket 014: `sandbox-011.toml` → 6 passed (blocked, no PR, colorama in Callouts, no requirements.txt). Other stops graded on synthetic runs (`test_a_blocked_auto_run_with_no_pr_passes`, `test_a_hard_stop_that_opened_a_pr_or_didnt_block_fails`) | pass |
| AC5 | SKILL.md § Auto mode "refuse `--auto` together with any live target"; guardrails row "A live target requested" | pass |
| AC6 | SKILL.md § Auto mode Resume line; state.md `auto` row "Resume sets it `false` unless `--auto` is given again" | pass |
| AC7 | campaign.md `**Auto**` paragraph; `AutoCampaignCaseTest` (4 tests: stacked + auto passes; no flag, gate not auto-approved, child waiting fail) | pass |
| AC8 | cases sandbox-010..014 for the plantable stops (narrowed at the Plan gate), each tested to pass on a correct run and fail on a PR/unblocked/flagless run plus a case-specific break (`test_case_specific_evidence_is_checked`) | pass |

## Notes
- The two live sandbox runs were driven by this session following the new rules (inline, small and standard-at-plan), not by an independent harness run: they show the cases grade real run artifacts, not that every model follows the rules. A headless run per case is the next evidence (docs/evals.md).
- Review ran in the same session (`review_context: shared`).
