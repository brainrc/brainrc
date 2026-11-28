# Verify: Reject duplicate pack names

Run at 2026-10-27T02:30:50Z on commit `d40a193`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 413 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `DuplicatePackTest.test_two_packs_with_one_name_are_refused` passes (validate, status, apply exit 1, nothing in HOME); manual: two scratch packs named `acme` → validate and apply print `ERROR pack name \`acme\` is used by both [one] and [two]`, apply exit 1, only `apply.lock` created | pass |
| AC2 | `test_doctor_reports_duplicate_names` passes; manual: doctor `FAIL pack name \`acme\` is used by both [one] and [two]`, fix names `pack.toml` and `enabled = false` | pass |
| AC3 | `test_a_pack_named_core_is_refused` passes (validate, apply; and `validate --pack` names the pack's dir) | pass |
| AC4 | `test_key_and_name_may_differ` passes | pass |

## Notes
- Inline mode (size small): implemented and reviewed in one context. Self-review found that `validate --pack` on a pack named `core` would say "core and core"; fixed in the same commit, labelled by the pack's directory.
- apply's closing line is still "Nothing written. Rename one of each pair, then re-run." (shared with item collisions).
