# Verify: Quiz the run's owner before the Deliver gate can be approved

Run at 2026-10-24T04:08:12Z on commit `84c0b9c`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 315 passed, 0 failed |
| Lint | — | not configured |
| Build | — | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: 26 skills, 10 agents |
| Plan / diff | — | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `agents/examiner.md`: frontmatter `name: examiner`, `tools: Read, Grep, Glob`; Questions section lists the 4 kinds and the `file:line` per question, no answers; handoff under 150 words | pass |
| AC2 | `SKILL.md` Deliver stage step 0 and Run step 4; `lifecycle.md` stage 6 row, details, and § Understand quiz (quiz before the gate, early `approve` refused and not recorded) | pass |
| AC3 | `lifecycle.md` § Understand quiz step 1 and `examiner.md` Questions: 1 / 2 / 3–5, plus 1 `risk` per trigger; "Every size runs it", unattended runs wait | pass |
| AC4 | `lifecycle.md` § Understand quiz step 3: multiple-choice pop-up with 3–4 shuffled choices; a right pick is understood, a wrong pick gets an explanation with `file:line` and a rephrased question with fresh choices; passes only when all are understood (revised at the owner's request in fb82aac, then 2e09910) | pass |
| AC5 | `state.md` example and `metrics.understanding` row define `asked`, `first_try`, `after_explanation`, `rounds` | pass |
| AC6 | `templates/retro.md` Understanding row (asked / first try / after explanation / rounds) | pass |
| AC7 | `templates/pr-body.md` § Check your understanding, questions only | pass |
| AC8 | `fallback.md` § Understand quiz: engine plays examiner from the artifacts only, then grades | pass |
| AC9 | `docs/spec-agent.md` § Understand quiz, flow diagram, roles table | pass |
| AC10 | `evals/cases/sandbox-001.toml` and `sandbox-003.toml` `min = 1` on `metrics.understanding.asked`; `tests/test_evals.py::CheckTest::test_state_min` passes (pass, below min, missing) | pass |
| AC11 | E2E on sandbox ticket 001 with the owner answering: Q1 partial → missed → understood, Q2 missed → partial → partial → understood, then Deliver approved; `evals.py check` 14/14; recorded in `docs/e2e-runs.md` | pass |
| AC12 | both checks above exit 0 | pass |

## Notes
AC11 ran in a scratch copy of the sandbox, not in this repo. Its `log.md` holds every round.
The review ran in a fresh subagent (`review_context: fresh`). Its 2 MEDIUM and 4 LOW findings
are fixed in 75e1512 and 84c0b9c.
