# Verify: brainrc uninstall

Run at 2026-11-10T17:20Z on commit `b594ea7`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 790 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 790 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `UninstallTest.test_configs_match_the_pre_apply_state_plus_the_users_later_edits` | pass |
| AC2 | `test_works_after_the_checkout_is_deleted`, `test_a_broken_harnesses_file_falls_back_to_the_manifest` | pass |
| AC3 | `test_configs_match_the_pre_apply_state_plus_the_users_later_edits`, `test_a_settings_file_it_cant_parse_is_left_and_reported` | pass |
| AC4 | `test_configs_match_the_pre_apply_state_plus_the_users_later_edits`, `test_the_settings_home_keeps_only_local_config` | pass |
| AC5 | `test_purge_deletes_the_settings_home`, `test_dry_run_changes_nothing` | pass |
| AC6 | `test_the_file_init_moved_aside_is_put_back` | pass |
| AC7 | `test_nothing_applied_means_nothing_to_do`, `test_a_second_uninstall_finds_nothing`, `test_apply_after_uninstall_reinstalls` | pass |

## Notes
The ticket's done-when ("harness configs match their pre-apply backups, except for the user's own later edits") is AC1.
