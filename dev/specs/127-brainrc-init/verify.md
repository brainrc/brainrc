# Verify: brainrc init

Run at 2026-11-10T17:02Z on commit `ed3ebf2`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 779 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 779 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `InitTest.test_init_then_apply_has_no_conflict_and_keeps_the_users_text`, `test_without_init_apply_reports_the_conflict` | pass |
| AC2 | `test_interactive_answers_choose_harnesses_and_adoptions`, `test_interactive_end_of_input_takes_the_defaults`, `test_without_a_terminal_it_asks_for_yes_or_harness`, `test_yes_manages_every_installed_harness_and_writes_nothing_new` | pass |
| AC3 | `test_harness_writes_enabled_and_keeps_the_rest_of_the_file`, `test_an_unknown_harness_is_an_error_and_writes_nothing`, `SetEnabledTest` | pass |
| AC4 | `test_init_then_apply_has_no_conflict_and_keeps_the_users_text`, `test_a_link_to_the_users_own_file_is_moved_and_its_target_kept`, `test_a_link_brainrc_made_is_left_alone` | pass |
| AC5 | `test_same_text_in_two_files_is_adopted_once`, `test_running_init_again_on_a_restored_file_adds_no_second_rule`, `test_different_text_gets_its_own_rule`, `test_an_empty_file_or_a_dangling_link_is_moved_without_a_rule` | pass |
| AC6 | `test_dry_run_writes_nothing`, `test_no_adopt_leaves_the_file_and_says_so` | pass |
| AC7 | `test_init_is_refused_while_an_old_home_is_unmigrated` | pass |

## Notes
The ticket's done-when ("init then apply → no CONFLICT, and the user's text still loads") is AC1.
