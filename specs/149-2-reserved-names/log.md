# Log 149-2-reserved-names

## engine · intake · done
2026-11-03T13:39:44Z

Split child 149.2 of gh:149 (campaign member 6), base 149-1-namespaced-skills. Size: small (validate.py + one test file). Mode: inline. Light spec written by the engine from parent AC4-AC6.

## engine · Spec gate · auto-approved
2026-11-03T13:39:44Z

⛔ Spec gate: 149-2-reserved-names. 3 criteria; reserved list per parent Q1 default. Plan: skipped (small); one-task plan written by the engine.

## engine · T1 · done (inline)
2026-11-03T13:42:04Z

**Did:** RESERVED_SKILL_NAMES and a core-only check in _validate_source; tests/test_reserved_names.py; patch fragment.
**Evidence:** red: 4 assertion failures (validate exited 0 on a core `init` etc.), 2 AttributeError (constant missing); then tests.test_reserved_names OK; validate OK (32 skills); full suite OK (1 skipped). AC3 is pinned by the existing test_name_collision_writes_nothing.
**Changed files:** brainrc/validate.py, tests/test_reserved_names.py, changelog.d/149-2-reserved-names.md

## code-reviewer · batch · done
2026-11-03T13:45:22Z

**Findings:**
- MEDIUM tests:33: AC2 pack half untested → fixed (pack `status` skill test).
- MEDIUM tests:33: AC3 via validate untested → fixed (core/pack duplicate through validate).
- LOW tests:35: exemption test only checked membership → fixed (validate output has no "reserved"); mutation check: forcing the exemption off fails 3 tests.
- LOW validate.py:135: uses the dir name → accepted (name must equal dir).

## engine · verify · done
2026-11-03T13:45:22Z

771 OK (1 skipped); validate OK; gitleaks no leaks. verify.md written. Drafts written by the engine (inline run).

## engine · child verified
2026-11-03T13:45:22Z

Campaign member 6 (149.2) verified. 149.3 starts from this branch.
