# Verify: Only touch harnesses that are installed

Run at 2026-11-10T16:52Z on commit `1af95cf`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 758 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 758 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `InstalledHarnessTest.test_only_claude_installed_gets_only_claude_changes` | pass |
| AC2 | `test_only_claude_installed_gets_only_claude_changes`, `test_status_says_what_it_skips_and_writes_nothing`, `test_a_disabled_harness_is_not_reported_as_missing` | pass |
| AC3 | `test_enabled_true_in_the_local_file_forces_a_harness`, `test_a_harness_only_in_the_local_file_is_managed`, `test_home_key_sets_what_counts_as_installed`; `ConfigErrorTest.test_harness_only_in_local_file_warns_and_still_loads` | pass |
| AC4 | `test_a_harness_installed_later_is_picked_up`, `test_uninstalled_harness_is_never_recreated` | pass |
| AC5 | `test_only_a_missing_harness_is_refused` | pass |
| AC6 | `test_apply_records_the_managed_harnesses`, `test_manifest_follows_full_applies_and_keeps_entries_outside_only`, `test_manifest_keeps_a_moved_checkouts_old_root`, `test_an_unreadable_manifest_is_rewritten` | pass |
| AC7 | `test_doctor_is_clean_after_apply`; `DoctorTest.test_a_harness_that_is_not_installed_is_skipped_not_reported` | pass |

## Notes
- Mutation check: `tests/test_installed_harnesses.py` against the base `brainrc/` fails 10 of 14 tests; the 4 that pass pin behavior that must not change (a later install, forcing by `enabled = true`, a disabled harness, a local-only harness).
- Existing suites that apply into a fake HOME now create every harness's directory first (`install_harnesses`), and "nothing written" checks look for files and links instead of an empty HOME. One doctor test changed on purpose: a missing harness is no longer a WARN.
- Reviewed inline (one context), so `review_context: shared`.
