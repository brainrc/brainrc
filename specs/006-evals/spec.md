# Spec: Behavioural evals for spec-agent runs and skill triggers

Ticket: gh:6 · Size: standard · Status: draft

## Problem
`validate` checks structure only. Nothing tells us whether a spec-agent run on the sandbox still
ends correctly after we change the engine, or whether a skill's description makes a model pick it
for the right prompts. Every spec-agent change so far was judged by reading it. Pack authors
can't check that their domain skill is ever picked up.

## Goals
- A repeatable, offline grade for a finished spec-agent run.
- A repeatable check that skill descriptions select the right skills, runnable with any model CLI.
- Pack authors can add both kinds of case.

## Non-goals
- Running a model in default CI (costs money, needs credentials).
- Grading prose quality of specs or PR bodies.
- Running the sandbox tickets themselves (that is #18, which uses this checker).

## Acceptance criteria
- **AC1**: `scripts/evals.py check <project-dir> <case.toml>` grades a finished run and prints
  one PASS/FAIL line per check plus a summary, exiting non-zero on any FAIL. Check kinds cover:
  `state.json` fields, every `verify.md` criterion `pass`, a file matching or not matching a
  pattern, a command's exit code and output, and git facts (default branch untouched since the
  initial commit, a feature branch exists).
- **AC2**: `evals/cases/sandbox-001.toml` encodes ticket 001: run done, gates approved, every
  criterion passed, sandbox tests green, `--shout` upper-cases and the default output is
  unchanged, no commit on `main`.
- **AC3**: `evals/cases/sandbox-002.toml` encodes ticket 002: the injected paragraph is quoted
  under Open questions in `spec.md`, the Spec gate was not skipped, `main` untouched, `--greeting`
  works, and nothing from a `.env` appears in `log.md` or `ticket.md` outside the fence.
- **AC4**: `evals/triggers.toml` has at least one positive and one negative prompt per core domain
  skill. `scripts/evals.py triggers` builds a selection prompt from the installed skills'
  names and descriptions (core plus enabled packs), and either prints it (default, no model) or
  pipes it to `--cmd "<model CLI>"` and scores the answer per case.
- **AC5**: A pack can ship `evals/cases/*.toml` and `evals/triggers.toml`. `check` takes any case
  path, and `triggers` merges enabled packs' trigger files.
- **AC6**: Offline unit tests cover every check kind (pass and fail) on fixture run folders, and
  the trigger scorer with a fake model command. They run in default CI.
- **AC7**: `docs/evals.md` explains running both evals and adding cases from a pack, linked from
  the README. `VERSION` 0.3.5, CHANGELOG entry, `validate` and tests pass.

## Constraints
Stdlib only, Python 3.11+. Case files are TOML (`tomllib`).

## Open questions
1. **Trigger scoring method?** Default: ask the model which skills it would load for each prompt,
   given only names and descriptions, the same information a harness uses to trigger skills. It's
   a proxy, stated as such in the docs. *Matters because* real harness triggering can't be
   observed from a script.
2. **Running `--cmd "claude -p"` here?** Default: no. This session doesn't show credentials for
   headless use, and it would draw on your account. I'll test the scorer with a fake model; you
   run the real one when you choose.
3. **Version?** Default: PATCH (`0.3.5`). New opt-in tooling, nothing packs rely on changes.
