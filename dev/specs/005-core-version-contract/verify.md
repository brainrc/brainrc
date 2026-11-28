# Verify: Core version contract for packs, and a CHANGELOG

Run at 2026-10-05T12:54:42Z on commit `690a473`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 46 tests, 0 failed (35 before) |
| Lint | — | not configured |
| Build | — | not applicable |
| Validate | `python3 scripts/aicfg.py validate` | pass: OK, 20 skills, 9 agents, 5 commands |
| Sandbox (CI step) | `python3 -m unittest -q` in `examples/sandbox` | pass |
| Plan / diff | — | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `VERSION` = `0.1.0`, read only by `core_version()`; `PackValidateTest.test_invalid_core_version_fails` | pass |
| AC2 | `test_compatible_pack_has_no_version_message`; `test_apply_layers_pack_on_core` (fixture pins `>=1.0, <2`, ends "Everything in sync.") | pass |
| AC3 | `test_incompatible_pack_fails`, `test_incompatible_enabled_pack_fails_plain_validate`; manual: `validate --pack` on a `>=9` pack → `ERROR acme:pack.toml: requires_core \`>=9\` is not satisfied by core 0.1.0`, exit 1 | pass |
| AC4 | `test_incompatible_pack_writes_nothing` (status and apply, HOME empty); manual: `apply` with temp HOME → exit 1, "Nothing written", 0 entries in HOME | pass |
| AC5 | `test_missing_requires_core_warns`, `test_pack_without_requires_core_applies_with_warning`; manual: `WARN ... no \`requires_core\``, exit 0 | pass |
| AC6 | `VersionConstraintTest.test_rejects_malformed` (9 inputs incl. `latest`, `>>1`); `test_malformed_requires_core_fails` (shows syntax) | pass |
| AC7 | `test_disabled_incompatible_pack_is_not_checked` | pass |
| AC8 | `CHANGELOG.md` 0.1.0 entry covers every roadmap Done item; `[pack contract]` marker; roadmap now links to it | pass |
| AC9 | `docs/packs.md`: `requires_core` in example, Compatibility section (syntax, outcomes, bump policy) | pass |
| AC10 | 11 new tests cover AC2–AC7; full suite and validate pass | pass |

## Notes
- Manual CLI checks ran on a throwaway pack, repo copy, and HOME under `mktemp -d`, deleted afterwards.
- F1 (found at verify): the warning's suggested pin now matches the documented policy.
