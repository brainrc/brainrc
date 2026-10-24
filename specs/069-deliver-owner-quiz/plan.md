# Plan: Quiz the run's owner before the Deliver gate can be approved

Spec: [spec.md](spec.md) · Status: draft

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** new role `examiner` (a tenth agent, installed by `aicfg apply` like the rest); new `state.quiz` field and `metrics.understanding`; eval `state` check gains `min`. All additive.
- **Migrations / data changes:** none. Runs started before this have no `quiz`; resume at deliver treats it as `pending` and runs the quiz.
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none (released by the normal changelog workflow)
- **Destructive or replacing changes:** none

## Approach
The quiz is the first step of the `deliver` stage, after the VERSION re-check and before the gate
message, so nothing outward can run first. The engine writes the diff to
`.runs/deliver-diff.patch` (the examiner has no Bash) and dispatches `examiner` with `spec.md`,
`plan.md`, `verify.md`, the review findings in `log.md`, and that patch. The examiner returns the
questions in its handoff: kind, the `file:line` tested, and the question, never the answer. The
engine asks one question at a time and grades each free-text answer against the diff. A `partial`
or `missed` answer gets a short explanation with a `file:line` pointer and a rephrased question on
the same point. Each round is appended to `log.md` as one `## examiner · quiz` block.

`state.quiz` (`pending` | `passed`) is what gates approval. While it isn't `passed`, an
`approve` gets this reply: "the quiz comes first". The approval isn't recorded, and nothing
counts as gate rework. Once every question is `understood`, the engine adds the questions to
`pr-body.md` under "Check your understanding", then presents the gate. In inline and fallback
mode the engine plays examiner itself (fallback.md step 2's role switch). Its questions come only
from the artifacts and the patch, never from its own notes.

Count: trivial 1, small 2, standard 3–5, +1 `risk` for each touched trigger category (security,
IAM, migration, prod). Large never reaches deliver. Metrics: `asked` counts the examiner's
questions, `first_try` the ones understood on the first answer, `after_explanation` the ones
understood after at least one explanation, and `rounds` every answer graded (≥ `asked`).

Evals: the `state` check gets `min = <number>`, which passes when the field is a number ≥ min.
That reuses `_field` and keeps the kind list unchanged.

## Files
| File | Change |
|---|---|
| `agents/examiner.md` | new role |
| `skills/spec-agent/SKILL.md` | roles row; Deliver stage step 0 (quiz) and approval rule |
| `skills/spec-agent/references/lifecycle.md` | deliver row and details; gate refusal; question count |
| `skills/spec-agent/references/fallback.md` | engine writes and grades questions |
| `skills/spec-agent/references/state.md` | `quiz`, `metrics.understanding` |
| `skills/spec-agent/templates/retro.md` | Understanding row |
| `skills/spec-agent/templates/pr-body.md` | Check your understanding section |
| `docs/spec-agent.md`, `docs/install.md` | roles table, flow diagram, Understand step |
| `scripts/evals.py`, `tests/test_evals.py`, `docs/evals.md` | `min` on state check |
| `evals/cases/sandbox-001.toml`, `sandbox-003.toml` | `metrics.understanding.asked` min 1 |
| `changelog.d/069-deliver-owner-quiz.md` | fragment, `bump: patch` |
| `docs/e2e-runs.md` | E2E run record |

## Risks
- The engine gives answers away in its own questions (inline mode), mitigated by having it write the questions from the artifacts only and never quote a line that answers the question.
- SKILL.md grows, mitigated by keeping the detail in lifecycle.md and adding only a few lines to SKILL.md.
- Resuming mid-quiz, mitigated by `state.quiz`, which stays `pending` until every question passes. A resume re-asks every question that isn't yet passed (read from `log.md`).

## Test strategy
AC10 gets unit tests in `tests/test_evals.py` (`min` passes and fails, plus a missing field).
The docs criteria (AC1–9) are checked by grep in verify. AC11 is the E2E run with the owner.
AC12 is the `validate` run plus the full unit test suite.

## Tasks
- [ ] **T1** [agent: implementer] Examiner role and its docs
  - files: `agents/examiner.md`, `docs/spec-agent.md`, `docs/install.md`
  - criteria: AC1, AC9
- [ ] **T2** [agent: implementer] Engine: quiz in the Deliver stage, approval refusal, fallback path
  - files: `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/lifecycle.md`, `skills/spec-agent/references/fallback.md`, `changelog.d/069-deliver-owner-quiz.md`
  - criteria: AC2, AC3, AC4, AC8
  - after: T1
- [ ] **T3** [agent: implementer] State, retro, and PR body records
  - files: `skills/spec-agent/references/state.md`, `skills/spec-agent/templates/retro.md`, `skills/spec-agent/templates/pr-body.md`
  - criteria: AC5, AC6, AC7
- [ ] **T4** [agent: implementer] Eval `min` check and sandbox cases
  - files: `scripts/evals.py`, `tests/test_evals.py`, `docs/evals.md`, `evals/cases/sandbox-001.toml`, `evals/cases/sandbox-003.toml`
  - criteria: AC10, AC12
- [ ] **T5** [agent: engine + owner] E2E run on a sandbox ticket, recorded
  - files: `docs/e2e-runs.md`
  - criteria: AC11
  - after: T2, T3, T4
