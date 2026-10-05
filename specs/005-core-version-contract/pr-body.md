Add a core version that packs can pin with requires_core

## Why
Packs depend on core's extension API, but core had no version. A breaking change in core broke packs silently, and pack authors found out only when spec-agent misbehaved.

## What changed
- `VERSION` (0.1.0) is the core version. Packs declare the versions they support with `requires_core = ">=0.1, <0.2"` in `pack.toml`.
- `validate` and `validate --pack` fail on an incompatible or malformed `requires_core`, and on an invalid `VERSION`.
- `status` and `apply` refuse to run with an incompatible pack enabled. They write nothing, like a name collision. Disabled packs aren't checked.
- A pack without `requires_core` still works. Both commands print a warning that suggests the pin the docs recommend.
- `CHANGELOG.md` now holds shipped work, with pack-contract changes tagged. The roadmap's Done list moved there. `docs/packs.md` documents the syntax and the bump policy.

Blast radius: machines with packs enabled. Existing packs without `requires_core` keep working and print a warning on every `status`, `apply` and `validate`. No change for machines without packs.

## Acceptance criteria
- [x] AC1: single core version, validated, verified by `test_invalid_core_version_fails`
- [x] AC2: compatible pack passes silently, verified by `test_compatible_pack_has_no_version_message`
- [x] AC3: incompatible pack fails validate, verified by `test_incompatible_pack_fails` and a manual CLI run
- [x] AC4: incompatible pack blocks status/apply with nothing written, verified by `test_incompatible_pack_writes_nothing` and a manual run in a temp HOME
- [x] AC5: missing `requires_core` warns, verified by `test_missing_requires_core_warns`
- [x] AC6: malformed constraint fails with the syntax, verified by `test_rejects_malformed`
- [x] AC7: disabled packs aren't checked, verified by `test_disabled_incompatible_pack_is_not_checked`
- [x] AC8: CHANGELOG with `[pack contract]` marker, roadmap links to it
- [x] AC9: `docs/packs.md` Compatibility section
- [x] AC10: 46 tests pass (11 new), `validate` passes

## How to verify
```
python3 -m unittest discover -s tests -q
python3 scripts/aicfg.py validate
```

## Follow-ups
- LOW: with packs enabled and `VERSION` missing, the "Update the pack or core" hint after the error is slightly off.

Spec: `specs/005-core-version-contract/spec.md` · Plan: `specs/005-core-version-contract/plan.md`
Closes #5

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
