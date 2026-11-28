Refuse to apply a pack that validate would fail

3 of 5 in epic #93 (E2: Config and pack loading).

## Why
`validate` and `validate --pack` check each pack's items: name prefix, frontmatter, references, hook fragments, and tripwires. `status` and `apply` didn't. A pack skill named `deploy` instead of `acme-deploy` was linked into every harness and `apply` exited 0. Only a later `validate` or `doctor` said anything, after the unprefixed name was already in the user's harness.

## What changed
- New `validate.pack_errors(srcs)` runs `_validate_source` on each pack, not core, with the agent and skill names of every source. These are the per-pack checks `validate --pack` runs.
- `cli._sync` calls it after the `requires_core` check and before anything is written. It prints each error, then ``Nothing written. Fix the pack (`… validate --pack <dir>` lists every problem), then re-run.``, naming only the failing packs, and returns 1. This covers both `status` and `apply`.
- `docs/troubleshooting.md` "Pack errors" says `apply` checks first. The `aicfg-config` living spec gets "Apply checks packs first".

## Acceptance criteria
- [x] AC1: apply refuses an unprefixed pack skill and writes nothing, verified by `PackApplyCheckTest.test_unprefixed_skill_is_refused`
- [x] AC2: status reports the same and exits 1, verified by the same test
- [x] AC3: any other pack validate error blocks apply, verified by `test_any_pack_validate_error_is_refused`
- [x] AC4: a valid pack links as before, verified by `test_a_valid_pack_links_as_before`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- A pack with one broken doc reference now blocks `apply`. This was chosen at the Spec gate, and it matches `doctor`, which already fails such a pack.

Spec: `specs/102-apply-validates-packs/spec.md` · Plan: `specs/102-apply-validates-packs/plan.md`
Closes #102
