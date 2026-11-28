Refuse two packs with the same name

2 of 5 in epic #93 (E2: Config and pack loading).

## Why
A pack's name comes from `name` in its `pack.toml`, or from its `packs.toml` key when that's missing. Two enabled packs with the same name share one hooks dir (`<hooks_dir>-<name>`), one rules label, and one set of owned hook entries. They overwrite each other, so `apply` never settles. `validate` passed them (`packs: acme, acme`). A pack named `core` was taken for core itself and failed with unrelated errors.

## What changed
- `Source` records its `packs.toml` key. The new `sources.duplicate_packs()` returns one error per shared name, `core` included: ``pack name `acme` is used by both [one] and [two]``.
- `validate`, `status`/`apply` (before anything is written), and `doctor` (as a FAIL whose fix names `pack.toml` `name` or `enabled = false`) run it next to the existing item-collision check.
- `docs/troubleshooting.md` gets a row in "Pack errors". The `aicfg-config` living spec gets "Unique pack names".

## Acceptance criteria
- [x] AC1: duplicate names fail validate, status, and apply, and apply writes nothing, verified by `DuplicatePackTest.test_two_packs_with_one_name_are_refused`
- [x] AC2: doctor reports it with a fix, verified by `test_doctor_reports_duplicate_names`
- [x] AC3: a pack named `core` is refused, verified by `test_a_pack_named_core_is_refused`
- [x] AC4: a key that differs from the name is fine, verified by `test_key_and_name_may_differ`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- Disabled packs aren't checked: their `pack.toml` isn't read.

Spec: `specs/101-reject-duplicate-pack-names/spec.md` · Plan: `specs/101-reject-duplicate-pack-names/plan.md`
Closes #101
