Add a tutorial for your first pack and domain skill

## Why
Nothing walked a newcomer from a fresh clone to a working extension that `aicfg` installs and spec-agent picks up. They had to assemble the steps from four docs and the example pack.

## What changed
- `docs/tutorial.md`: build a pack called `myteam` with one Protocol Buffers domain skill, validate it, enable and apply it, and check that spec-agent lists it. Every step has the exact command and what you should see. It ends with the pack's own CI and next steps (the example pack, contributing to core).
- `specs/013-tutorial/run-tutorial.sh` runs every `bash` block in the tutorial, in order, on a fresh clone with a temporary HOME. It passed on this branch.
- The README's "Adding content" section links the tutorial.
- `VERSION` 0.3.3.

It starts a minimal pack instead of copying the example pack, because renaming every `acme` string needs `sed -i`, which differs between macOS and Linux.

Blast radius: docs only.

## Acceptance criteria
- [x] AC1: fresh clone to an installed, validated pack with a domain skill
- [x] AC2: exact commands and expected output for each step
- [x] AC3: CI snippet and next steps
- [x] AC4: the runner executes the tutorial cleanly
- [x] AC5: README link, 0.3.3, checks pass

## How to verify
```
specs/013-tutorial/run-tutorial.sh
```

## Follow-ups
- LOW: the runner isn't in CI, so the tutorial's `requires_core` pin can go stale at the next MINOR bump unnoticed.

Spec: `specs/013-tutorial/spec.md` · Plan: `specs/013-tutorial/plan.md`
Closes #13

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
