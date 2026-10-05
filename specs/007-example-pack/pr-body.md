Add an example pack and validate it in CI

## Why
Pack authors had docs but nothing to copy, and nothing proved a realistic pack still passed after a core change. The example now fails the build when core breaks the pack contract or the docs drift.

## What changed
- `examples/pack-acme`: a working pack with `requires_core`, all four spec-agent extension points, a domain skill, an intake context skill, a rule, a command, a tripwire, and a README on copying it. It has two skills, not one, because `intake_context` needs its own.
- `ExamplePackTest` validates the example against the real `VERSION`, so local runs and pre-commit catch a break.
- The `validate` workflow validates the example as its own named step.
- `docs/packs.md` links to it. CHANGELOG has an Unreleased entry. No version bump.

Blast radius: CI gains one step. Nothing is linked or rendered on any machine unless someone lists the example in `packs.local.toml`.

Expect this: the example pins `<0.2`, so the next pack-contract bump (#8, #9) fails `ExamplePackTest` until that PR updates the example.

## Acceptance criteria
- [x] AC1: example passes `validate --pack` with no warnings, verified by `ExamplePackTest`
- [x] AC2: uses every extension point, verified by validate and a manual `apply` in a temp HOME
- [x] AC3: README covers copy, rename, enable, validate
- [x] AC4: a core bump outside `requires_core` fails the test, verified by a mutation check
- [ ] AC5: CI runs it as its own step, verify on this PR's `validate` job
- [x] AC6: `docs/packs.md` links to it
- [x] AC7: core validate and default apply unchanged

## How to verify
```
python3 -m unittest discover -s tests -q
python3 scripts/aicfg.py validate --pack examples/pack-acme
```

## Follow-ups
- LOW: the example rule uses a `Refs: ACME-123` trailer, while spec-agent writes `Refs <ref>`. Both work.

Spec: `specs/007-example-pack/spec.md` · Plan: `specs/007-example-pack/plan.md`
Closes #7

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
