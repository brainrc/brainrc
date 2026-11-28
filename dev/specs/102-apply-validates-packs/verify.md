# Verify: apply validates packs before linking

Run at 2026-10-27T02:35:14Z on commit `58622e4`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 417 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `PackApplyCheckTest.test_unprefixed_skill_is_refused` passes (apply exit 1, the prefix error, `validate --pack <dir>`, "Nothing written", empty HOME, no render); manual: scratch pack with `skills/deploy` → apply exit 1, only `apply.lock` created | pass |
| AC2 | same test runs `status` first: exit 1, same error | pass |
| AC3 | `test_any_pack_validate_error_is_refused` passes (missing `description`) | pass |
| AC4 | `test_a_valid_pack_links_as_before` passes; manual: after renaming to `acme-deploy`, apply exit 0 and links it into all five harnesses | pass |

## Notes
- Inline mode. Self-review: the closing hint named every pack, including passing ones; narrowed to the failing packs (`test_only_the_failing_pack_is_named`).
