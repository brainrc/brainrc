Render pack rules after core rules and release 0.2.0

## Why
Pack rules were interleaved with core rules by filename, so a pack's `15-acme.md` landed between core's `10-git.md` and `20-engineering.md`. Nothing in the rendered file said where a rule came from, and no doc said what happens when a pack rule disagrees with core.

## What changed
- **[pack contract]** Rendered instructions are now core rules, then each pack's rules as one block per pack in `packs.toml` order, then `*.local.md` rules. Pack and local blocks start with a comment label and one sentence telling the model they refine the rules above. A core-only render is byte-identical to before.
- `docs/formats.md` and `docs/packs.md` (new Rules section) state the order and the policy: later rules refine earlier ones and must not contradict them.
- `validate` fails when the newest CHANGELOG heading doesn't match `VERSION`, or an `## Unreleased` section exists. This enforces the every-PR-bumps rule from #30.
- `VERSION` 0.2.0. The example pack and the docs example now pin `">=0.2, <0.3"`.

Blast radius: every machine with packs enabled, on the next `apply`: pack rules move after core rules. Packs pinned `<0.2` now fail `validate` and block `apply` until they update `requires_core`. Machines without packs: no change.

Merge order: #30 (0.1.2) is also open. If it merges first, I'll merge main here and keep this PR at 0.2.0.

## Acceptance criteria
- [x] AC1: core, then pack blocks in source order, then local, verified by `RenderInstructionsTest` and a manual `apply`
- [x] AC2: a pack `15-*.md` lands after every core rule
- [x] AC3: pack and local blocks are labelled, core is not
- [x] AC4: core-only render unchanged, verified against main's renderer
- [x] AC5: order and refine policy documented
- [x] AC6: 0.2.0, tagged entry, example pin updated
- [x] AC7: CHANGELOG/VERSION check, verified by `ChangelogCheckTest`
- [x] AC8: 55 tests, `validate`, example validate pass

## How to verify
```
python3 -m unittest discover -s tests -q
python3 scripts/aicfg.py validate
python3 scripts/aicfg.py validate --pack examples/pack-acme
```

## Follow-ups
- none

Spec: `specs/009-rule-precedence/spec.md` · Plan: `specs/009-rule-precedence/plan.md`
Closes #9

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
