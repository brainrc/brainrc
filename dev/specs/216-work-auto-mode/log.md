# Log: 216-work-auto-mode

## engine · intake · done
2026-10-27T03:01:46Z

**Did:** Branch 216-work-auto-mode from main (ba3b622, v0.3.47). ticket.md from gh:216. Size large (engine gate rules, guardrails, campaign, state, work skill, PR template, eval grader; several policy questions), mode fallback, domains: scripting, offline only.

**Evidence:**
- read SKILL.md § Run, references/guardrails.md, docs/e2e-runs.md (self-approval finding), docs/evals.md, evals/cases

**Changed files:** specs/216-work-auto-mode/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-27T03:01:46Z

**Did:** Wrote spec.md: 8 criteria, 5 open questions, proposed split into 3 children (single runs; evals; campaigns). Deltas for run-lifecycle and campaign-mode.

**Evidence:**
- `living_specs.py check` → would update run-lifecycle.md, campaign-mode.md

**Changed files:** specs/216-work-auto-mode/spec.md

**Open issues:** 5 open questions (defaults stated)

**Next:** Spec gate (large: split proposal)

## engine · Spec gate approved
2026-10-27T03:03:39Z

- User chose "Approve, no split": resized large → standard (one run, Plan gate added). Open questions 1-5 resolved with their defaults. Spec change after approval (wording only): size line, resolved note, split marked not taken.

## architect · plan · done
2026-10-27T03:05:05Z

**Did:** Wrote plan.md: 4 tasks (engine rules; campaigns; eval tickets/cases; campaign eval). No aicfg code change; existing eval check kinds suffice.

**Evidence:**
- read SKILL.md, guardrails.md, state.md, lifecycle.md, fallback.md, campaign.md, templates/pr-body.md, scripts/evals.py, tests/test_evals.py, examples/sandbox

**Changed files:** specs/216-work-auto-mode/plan.md

**Open issues:** Callouts: new flag + state field; outward-action exception (approved as Q2). Design choice to narrow AC8 to plantable stops: decide at the Plan gate.

**Next:** Plan gate

## engine · Plan gate approved
2026-10-27T03:25:25Z

- AC8 narrowed to plantable hard stops (approved).

## implementer · T1 · done
2026-10-27T03:27:03Z

**Did:** `## Auto mode` in SKILL.md with pointers from § Run 3-4 and § Deliver stage; guardrails auto stop rows and the outward exception; `auto` in state.md; fallback review line; `## Decisions made without you` in templates/pr-body.md; `--auto` in work/SKILL.md.

**Evidence:**
- docs-only task (no red test); `python3 -m unittest discover -s tests` → 427 passed; `validate` OK (plugin manifests not stale)

**Changed files:** the six files in T1

**Open issues:** none

**Next:** review (each)

## code-reviewer + security-reviewer · T1 · changes-requested → fixed
2026-10-27T03:27:03Z

**Did:** Reviewed the T1 diff against spec.md. review_context: shared.

**Evidence:**
- HIGH `--auto` + `--local`: Deliver bullet would push; local-only must win → added
- MEDIUM (security) no explicit statement that `--auto` never covers the watch Push gate (spec non-goal) → added

**Changed files:** skills/spec-agent/SKILL.md (fix folded into the T1 commit before it was made)

**Open issues:** none

**Next:** T2

## implementer · T2 · done
2026-10-27T03:27:31Z

**Did:** `**Auto**` paragraph in campaign.md § Ordered shape: flag inherited by children, all gates auto-approved, stacked draft PRs, a blocked child pauses later ones and the stack opens no PRs; playbook + --auto refused.

**Evidence:**
- docs-only; `validate` OK

**Changed files:** skills/spec-agent/references/campaign.md

**Open issues:** none

**Next:** T3

## implementer · T3 · done
2026-10-27T03:31:16Z

**Did:** tickets 011-017, cases sandbox-008..014 (existing kinds), README rows, `AutoCaseTest` (7 tests: passes on correct fake runs, fails per mutated field).

**Evidence:**
- mutation: removing `ticket.pr present=false` from sandbox-011 made `test_a_hard_stop_that_opened_a_pr_or_didnt_block_fails` fail; restored
- `python3 -m unittest discover -s tests` → 434 passed; `validate` OK

**Changed files:** examples/sandbox/tickets/011-017, examples/sandbox/README.md, evals/cases/sandbox-008..014.toml, tests/test_evals.py

**Open issues:** none

**Next:** T4

## implementer · T4 · done
2026-10-27T03:32:58Z

**Did:** ticket 018 (epic 004's children with --auto), case sandbox-015, README row, `AutoCampaignCaseTest` (4 tests).

**Evidence:**
- `python3 -m unittest discover -s tests` → 438 passed; `validate` OK

**Changed files:** examples/sandbox/tickets/018-auto-greeting-epic.md, examples/sandbox/README.md, evals/cases/sandbox-015.toml, tests/test_evals.py

**Open issues:** none

**Next:** batched review

## code-reviewer · batched review · changes-requested
2026-10-27T03:35:40Z

**Did:** Reviewed `git diff bee24f1..HEAD` (T2-T4) against spec.md. review_context: shared.

**Evidence:**
- HIGH sandbox-014: CRITICAL finding comes after implement, so a correct run has `eval(` on its branch; `greet.py absent eval(` fails a correct run → check log.md for the finding
- MEDIUM SKILL.md § Auto mode: size large didn't say to write the spec + split before stopping (sandbox-012 expects it)

**Changed files:** none

**Open issues:** none after F1, F2

**Next:** F1, F2

## implementer · F1, F2 · done
2026-10-27T03:35:40Z

**Did:** F1 bb28e39: large stops after spec.md with its Proposed split. F2 2313d50: sandbox-014 checks log.md for the CRITICAL finding; ticket 017 and README text updated; test fixtures follow. Re-review of the fix diff: no findings.

**Evidence:**
- `python3 -m unittest discover -s tests` → 438 passed; `validate` OK

**Changed files:** skills/spec-agent/SKILL.md; evals/cases/sandbox-014.toml, tickets/017, README, tests/test_evals.py

**Open issues:** none

**Next:** verify

## verifier · verify · done
2026-10-27T03:39:33Z

**Did:** verify.md: AC1-AC8 pass. Live sandbox runs: ticket 011 (--auto, small) graded by sandbox-008 → 17/17; ticket 014 (--auto, new dependency) graded by sandbox-011 → 6/6.

**Evidence:**
- `python3 -m unittest discover -s tests` → 438 passed; `validate` OK

**Changed files:** specs/216-work-auto-mode/verify.md

**Open issues:** live runs were driven by this session (noted)

**Next:** document

## doc-writer · document · done
2026-10-27T03:39:33Z

**Did:** docs/spec-agent.md "Auto mode" + command row, docs/evals.md cases, living deltas (run-lifecycle, campaign-mode), changelog fragment, pr-body.md, ticket-comment.md.

**Evidence:**
- `living_specs.py apply` → updated 2 areas; `validate` OK

**Changed files:** docs/spec-agent.md, docs/evals.md, specs/living/*, changelog.d/216-work-auto-mode.md, drafts

**Open issues:** none

**Next:** Deliver gate
