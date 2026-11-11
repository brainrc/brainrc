Reject core skills named after harness built-ins in validate

5 of 6 in epic #113, stacked on #<PREV_PR>. Retarget to `main` before merging. Part 2 of 3 of #149.

## Why
Part 1 moved the colliding core skills to `brainrc-*` names. Nothing stopped a new core skill from taking a built-in name again.

## What changed
- `brainrc/validate.py`: `RESERVED_SKILL_NAMES` (`review`, `plan`, `init`, `help`, `status`, `compact`). `validate` fails on a core skill with one of those names unless it is a deprecated alias kept until 0.6.0. Packs are not checked; their skills already carry the pack prefix.
- `tests/test_reserved_names.py`: reserved core names fail, the shipped tree passes, the aliases are exempt, pack skills are not checked, and the core/pack duplicate error still fires.
- `changelog.d/149-2-reserved-names.md` (patch).

## Acceptance criteria
- [x] AC1: a core `init`/`help`/`status`/`compact` fails, naming the skill (`tests.test_reserved_names`)
- [x] AC2: the shipped tree passes; `review` and `plan` aliases are exempt; a pack `status` skill gets no reserved error
- [x] AC3: "defined in both" still fires through validate and sync

## How to verify
```
python3 -m unittest tests.test_reserved_names
python3 scripts/brainrc.py validate
python3 -m unittest discover -s tests
```
771 tests OK (1 skipped) on this branch.

## Decisions made without you
- Size small, so it ran inline: the engine wrote the spec and plan from the parent spec's AC4-AC6. Spec gate auto-approved; plan gate skipped (small).
- The reserved list is the parent spec's default. The repo has no verified list of harness built-ins; it is one constant to extend.
- Ticket comment not posted.

## Follow-ups
- Check the reserved list against each harness's built-in commands.

Spec: `specs/149-2-reserved-names/spec.md` · Parent: `specs/149-namespace-core-skills/spec.md`

Refs #149

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01Hn6pdU7RJ1sLQqc3fDP7Sa
