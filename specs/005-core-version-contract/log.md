## analyst · spec · done
2026-10-05T05:45:35Z

**Did:** Wrote spec.md from ticket gh:5: version source of truth, requires_core checks in validate and apply, CHANGELOG, docs.

**Evidence:**
- read `scripts/aicfg.py` (load_pack, sources, cmd_sync, cmd_validate) to confirm current behaviour

**Changed files:** `specs/005-core-version-contract/spec.md`

**Open issues:** 10 criteria, 5 open questions (each with a recommended default)

**Next:** Spec gate

## architect · plan · done
2026-10-05T12:47:34Z

**Did:** Wrote plan.md: VERSION file as source of truth, three helpers in aicfg.py shared by validate and sync, docs and CHANGELOG.

**Evidence:**
- read `scripts/aicfg.py` (load_pack, cmd_sync, cmd_validate, _validate_pack) and `tests/test_aicfg.py` fixtures

**Changed files:** `specs/005-core-version-contract/plan.md`

**Open issues:** 4 tasks; callout: new optional pack.toml key `requires_core` and root `VERSION` file (public contract)

**Next:** Plan gate
