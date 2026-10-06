Add evals: grade spec-agent runs and score skill selection

## Why
`validate` only checks that files are well formed. Nothing told us whether a spec-agent run on the sandbox still ends correctly after a change, or whether a skill's description makes a model pick it. Every spec-agent change so far was judged by reading it.

## What changed
- `scripts/evals.py check <project> <case.toml>` grades a finished run: `state.json` fields, every criterion in `verify.md`, file patterns, command results, `main` untouched, branch exists, no `.env` committed. One PASS/FAIL line per check, non-zero exit on any failure.
- `evals/cases/sandbox-001.toml` and `sandbox-002.toml` encode the two sandbox tickets, including that 002's planted instructions are flagged and not followed.
- `scripts/evals.py triggers` builds one prompt from every installed skill's name and description plus the cases in `evals/triggers.toml` (15 cases: a positive and a negative per domain skill). It prints the prompt, or scores a model CLI's reply (`--cmd "claude -p"`) or a saved one (`--answer`). It's a proxy for real triggering, and the docs say so.
- Packs can ship `evals/triggers.toml` (merged when enabled) and `evals/cases/*.toml`.
- `docs/evals.md`, linked from the README. `VERSION` 0.3.5.

Blast radius: new opt-in tooling and 17 offline tests in CI. Nothing calls a model unless you pass `--cmd`.

## Acceptance criteria
- [x] AC1: run checker with seven check kinds
- [x] AC2: sandbox-001 case (first real run in #18)
- [x] AC3: sandbox-002 case (first real run in #18)
- [x] AC4: trigger cases and runner, positive and negative per domain skill
- [x] AC5: packs can add both kinds
- [x] AC6: offline tests in CI
- [x] AC7: docs, README link, 0.3.5

## How to verify
```
python3 -m unittest tests.test_evals
python3 scripts/evals.py triggers | head
```

## Follow-ups
- The sandbox cases haven't graded a real run yet. #18 runs both tickets and grades them.

Spec: `specs/006-evals/spec.md` · Plan: `specs/006-evals/plan.md`
Closes #6

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
