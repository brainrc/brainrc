spec-agent fixes from the rename campaign's retros

## Why
The rename campaign's retros found five gaps that cost a retry or nearly shipped a bug. The
biggest one: a `minor` fragment nearly released 0.5.0, the version the deprecation warnings
promise removes the `aicfg` names, before they were removed.

## What changed
- `validate` and `release` refuse fragments whose bump would release `SHIM_REMOVED_IN` or later
  while the deprecated names still exist. A `patch` bump, or a change that removes them, is fine.
- Tests clear `XDG_CONFIG_HOME` in the shared `TempRepoCase`, so they behave the same locally as
  on CI runners.
- spec-agent rules:
  - An auto Spec gate is never approved while `living_specs.py check` fails.
  - Dispatches quote spec and plan rules word for word.
  - The analyst writes MODIFIED blocks as full requirement text.

## Acceptance criteria
- [x] AC1: premature removal bump refused, verified by two ReleaseTest cases (red first)
- [x] AC2: XDG isolation in the base case; suite passes with `XDG_CONFIG_HOME` set
- [x] AC3: the three rules are in SKILL.md, handoff.md and agents/analyst.md

## How to verify
```
python3 -m unittest discover -s tests
XDG_CONFIG_HOME=/home/runner/.config python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
```

## Decisions made without you
- Run inline (size small); Spec and Plan gates not stopped, per your instruction.
- The rules went into the existing sections, one sentence each, to keep the skill files short.
- Local ticket `specs/tickets/236-spec-agent-retro-fixes.md` (there is no GitHub issue).

## Follow-ups
- none

Spec: `specs/236-spec-agent-retro-fixes/spec.md` · Plan: `specs/236-spec-agent-retro-fixes/plan.md`
