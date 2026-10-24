Quiz the run's owner before the Deliver gate can be approved

## Why
spec-agent could take a ticket to a reviewed, tested PR while the person who ran `/work`, and who owns the PR, never had to understand the change. The Deliver gate asked for approval, not understanding.

## What changed
- New Understand quiz, the first step of the deliver stage. The owner answers 1 (trivial), 2 (small), or 3–5 (standard) questions, plus one `risk` question per security, IAM, migration, or prod trigger touched. Each question is a pop-up with 3–4 choices. The engine grades each pick against the diff. A wrong pick gets a short explanation with a `file:line` pointer and a rephrased question on the same point with fresh choices. The Deliver gate opens only when every question is understood. An earlier `approve` is refused and not recorded. No size or unattended run skips the quiz.
- New read-only `examiner` role (`agents/examiner.md`, `Read, Grep, Glob`) writes the questions from `spec.md`, `plan.md`, `verify.md`, the review findings, and a diff patch, so the engine can't write questions that contain their own answers. In inline and fallback mode the engine plays examiner from the artifacts only.
- `state.quiz` (`pending` | `passed`) gates approval and goes back to `pending` when Deliver rework changes the diff. `metrics.understanding` records `{ asked, first_try, after_explanation, rounds }`, and the retro has a matching row. The PR body gets a "Check your understanding" section with the questions only.
- Campaigns run one quiz over the combined diff before each Deliver gate and record the result in every member's state.
- Eval `state` checks accept `min = <n>`. Sandbox cases 001 and 003 require `metrics.understanding.asked` ≥ 1.
- Docs: Understand quiz section and examiner row in `docs/spec-agent.md`, `docs/evals.md`, `docs/install.md`, an E2E run in `docs/e2e-runs.md`, and a changelog fragment.

## Acceptance criteria
Most criteria describe engine behavior written in markdown and were checked by reading the cited text. AC10, AC11, and AC12 have executable evidence.

- [x] AC1: examiner role, read-only, kinds and `file:line`, no answers (read: `agents/examiner.md`)
- [x] AC2, AC3, AC4: quiz before the gate, sizes, multiple-choice pop-up, grading, refusal of an early approve (read: `SKILL.md`, `lifecycle.md`). AC4 changed twice at the owner's request during the Deliver quiz: free text to pick plus why (fb82aac), then to multiple choice only (2e09910).
- [x] AC5, AC6, AC7: state, retro row, PR body section (read: `state.md`, templates)
- [x] AC8: fallback path (read: `fallback.md`)
- [x] AC9: docs (read: `docs/spec-agent.md`)
- [x] AC10: `min` state check, verified by `tests/test_evals.py::CheckTest::test_state_min`
- [x] AC11: E2E on sandbox ticket 001 with a person answering. Each question took several rounds (partial, missed, then understood), and the gate opened only after both passed. `evals.py check` 14/14. This ran before the pop-up change and used free-text answers. #69's own Deliver quiz used the pop-up.
- [x] AC12: `aicfg.py validate` and 315 unit tests pass

## How to verify
```
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
python3 -m unittest tests.test_evals -k test_state_min -v
```

## Check your understanding
The run's owner answered these before delivery. Questions only, no choices; answers are in the run's `log.md`, so try them first.
1. why: Why does the engine save the diff to `.runs/deliver-diff.patch` before dispatching the examiner? (`skills/spec-agent/references/lifecycle.md:91`)
2. what-if: After the quiz passes, the owner requests a Deliver-gate change that alters the diff. What happens to the quiz? (`skills/spec-agent/references/lifecycle.md:113`)
3. where: In a batch campaign, where does the Understand quiz run? (`skills/spec-agent/references/campaign.md:77`)
4. what-if: A state check has `min = 1` and the field holds boolean `true`. What result does it give? (`scripts/evals.py:124`)
5. why: What happens to an `approve` sent while the quiz isn't passed yet? (`skills/spec-agent/references/lifecycle.md:111`)

## Follow-ups
- The metrics rollup (`scripts/retro_metrics.py`, `retro_report.py`) doesn't read `metrics.understanding` yet; deferred at the Spec gate.
- `deliver-diff.patch` can include a local ticket file's status line; consider excluding ticket files.

Spec: `specs/069-deliver-owner-quiz/spec.md` · Plan: `specs/069-deliver-owner-quiz/plan.md`
Closes #69
