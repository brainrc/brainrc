# Spec: CONTRIBUTING.md for human contributors

Ticket: gh:15 · Size: small · Status: draft

## Problem
The rules for changing this repo live in `AGENTS.md`, which is written for AI assistants.
A human contributor looks for `CONTRIBUTING.md`, finds nothing, and misses the setup, the
checks, the version-bump rule, and where generic vs pack content goes.

## Goals
- A human contributor finds setup, workflow, and PR expectations in the usual place.
- One copy of the rules, so humans and AI assistants follow the same ones.

## Non-goals
- Changing any rule.
- A code of conduct or governance docs.

## Acceptance criteria
- **AC1**: `CONTRIBUTING.md` covers setup (clone, `pre-commit install`), the change workflow
  (branch, checks, version bump, PR with `Closes #N`), optional spec-agent use (`/work gh:N`
  and what its `specs/` folder is), and where content goes (core vs pack).
- **AC2**: The rules stay in `AGENTS.md` only. `CONTRIBUTING.md` links to them and repeats no
  rule text. `AGENTS.md` links back to `CONTRIBUTING.md` for setup and workflow.
- **AC3**: README links `CONTRIBUTING.md`. `VERSION` 0.3.4 with a CHANGELOG entry. `validate`
  and tests pass. Every command in `CONTRIBUTING.md` runs as written.

## Constraints
Under ~50 lines. Prose follows the unslop rules.

## Open questions
1. **Which file holds the rules?** Default: `AGENTS.md`. AI tools load it every session (through
   `CLAUDE.md`), so moving the rules out would cost every session a file read.
