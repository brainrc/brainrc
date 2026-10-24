# Spec: Quiz the run's owner before the Deliver gate can be approved

Ticket: gh:69 · Size: standard · Status: approved

## Problem
spec-agent can take a ticket to a reviewed, tested PR while the person who ran `/work`, and who
will own the PR, never had to understand the change. The Deliver gate asks for approval, not for
understanding, so the owner can wave through a change they couldn't explain or roll back.

## Goals
- The owner shows they understand what changes and why before anything outward happens.
- Questions come from someone other than the engine, so they don't give away their own answers.
- Reviewers see the same questions, and runs record how much explaining the owner needed.

## Non-goals
- Quizzing PR reviewers (they only see the questions in the PR body).
- Scoring people, or storing answers anywhere except the run's own `log.md`.
- Multiple-choice questions, or any way to skip the quiz.

## Acceptance criteria
- **AC1**: Given the spec-agent package, when `agents/examiner.md` is read, then its frontmatter has `name: examiner`, `tools: Read, Grep, Glob`, and the body says it writes each question with its kind (`why`, `where`, `what-if`, `risk`) and the `file:line` it tests, never the answer, and ends with a handoff under 150 words.
- **AC2**: Given the Deliver stage in `SKILL.md` and `lifecycle.md`, when a run reaches deliver, then they say the quiz runs before the gate is presented and before any outward action, and an approval sent before the quiz is passed is refused.
- **AC3**: Given the question count rule, when it is read, then trivial asks 1, small 2, standard 3–5, plus 1 `risk` question when a security, IAM, migration, or prod trigger is touched; every size runs the quiz, unattended runs included (the quiz waits for the owner).
- **AC4**: Given the grading rule, when an answer is graded against the diff, then `understood` passes the question, and `partial` or `missed` gets a short explanation with a `file:line` pointer and a rephrased question on the same point; the quiz passes only when every question ends `understood`.
- **AC5**: Given `state.md`, when it is read, then `metrics.understanding` is documented as `{ asked, first_try, after_explanation, rounds }` with what each counts.
- **AC6**: Given `templates/retro.md`, when it is read, then it has an Understanding row with the same four numbers.
- **AC7**: Given `templates/pr-body.md`, when it is read, then it has a "Check your understanding" section that lists the questions without answers.
- **AC8**: Given `fallback.md`, when the run is inline or fallback, then it says the engine writes the questions (as the examiner role) and grades the answers itself.
- **AC9**: Given `docs/spec-agent.md`, when it is read, then it documents the Understand step.
- **AC10**: Given sandbox cases 001 and 003, when `scripts/evals.py check` runs on a finished run, then a check fails unless `metrics.understanding.asked` ≥ 1, and `tests/test_evals.py` covers the pass and fail sides of that check.
- **AC11**: Given one E2E run of a sandbox ticket, when the owner's first answer is wrong, then the log shows an explanation and a follow-up question, and the gate is approved only after the follow-up is `understood`; the run is recorded in `docs/e2e-runs.md`.
- **AC12**: Given the repo checks, when `aicfg.py validate` and the unit tests run, then both pass.

## Constraints
- Rules and skill files stay short: they load into model context.
- `scripts/evals.py` stays stdlib-only. Existing eval cases keep passing unchanged.
- Generic content only (public repo).

## Requirement changes

### Area: deliver-gate
Purpose: What must happen before a run's outward actions are allowed.
#### ADDED: Understand quiz before Deliver
The system SHALL quiz the run's owner with free-text questions from the read-only examiner role (or the engine in inline/fallback mode), sized by tier plus one risk question per touched trigger, before presenting the Deliver gate, for every size and unattended runs too. (AC1, AC2, AC3, AC8)
#### ADDED: Quiz grading and approval
The system SHALL grade each answer against the diff, explain a partial or missed answer with a `file:line` pointer and re-ask a rephrased question, and refuse Deliver approval until every question is understood. (AC2, AC4)
#### ADDED: Understanding record
The system SHALL record `metrics.understanding` (`asked`, `first_try`, `after_explanation`, `rounds`), show it in the retro, and list the questions without answers in the PR body. (AC5, AC6, AC7)

### Area: evals
#### ADDED: Minimum value state check
The eval harness SHALL let a `state` check require a numeric field to be at least a given value, used to require `metrics.understanding.asked` ≥ 1 on sandbox cases 001 and 003. (AC10)

## Open questions
Resolved at the Spec gate:
1. AC11: the owner answers the E2E quiz in this session before Deliver.
2. Metrics rollup: deferred to a follow-up issue.
3. Answers live in `log.md`, one `## examiner · quiz` block per round.
