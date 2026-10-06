Add CONTRIBUTING.md for human contributors

## Why
The rules for changing this repo lived only in `AGENTS.md`, which is written for AI assistants. A human contributor looking for `CONTRIBUTING.md` found nothing and missed the setup, the checks, the version-bump rule, and where team-specific content goes.

## What changed
- `CONTRIBUTING.md`: setup (`pre-commit install`), the change workflow (branch, pack vs core, version bump, checks, PR with `Closes #N`), how to use spec-agent and what its `specs/` folder is, and where to start reading.
- The rules stay in `AGENTS.md`, which now says they apply to humans too and links back to `CONTRIBUTING.md`. The only overlap is two workflow steps (run the checks, bump `VERSION`), kept in both because each audience needs them as steps.
- The README links `CONTRIBUTING.md`.
- `VERSION` 0.3.4.

Blast radius: docs only. `AGENTS.md` gains one line, loaded in every AI session in this repo.

## Acceptance criteria
- [x] AC1: setup, workflow, spec-agent, content placement
- [x] AC2: one copy of the rules, linked both ways
- [x] AC3: README link, 0.3.4, every command ran on a fresh clone

## How to verify
```
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
```

## Follow-ups
- none

Spec: `specs/015-contributing/spec.md` · Plan: `specs/015-contributing/plan.md`
Closes #15

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
