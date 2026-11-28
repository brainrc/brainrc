# Verify: Rebuild the CLI on argparse

Run at 2026-11-10T16:36Z on commit `8d5d8af`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 744 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 744 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `HelpTest.test_help_and_version_exit_zero`, `test_checkout_script_help_exits_zero` | pass |
| AC2 | `HelpTest.test_each_command_has_its_own_help` | pass |
| AC3 | `HelpTest.test_maintainer_commands_are_hidden_but_still_run` | pass |
| AC4 | `HelpTest.test_usage_errors_exit_two_on_stderr`; `BrainrcCommandTest.test_usage_names_brainrc_in_a_checkout` | pass |
| AC5 | `HelpTest.test_help_names_the_installed_command`; `InstalledModeTest.test_hints_name_the_installed_command` | pass |
| AC6 | `OnlyTest.test_apply_only_claude_touches_only_claude`, `test_status_only_reports_only_that_harness`, `test_several_harnesses_by_repeat_or_comma`, `test_other_harnesses_keep_their_links_and_hooks`, `test_disabled_harness_cleanup_waits_for_a_full_apply`; `OnlyInstalledTest.test_only_a_harness_without_hooks_keeps_the_hooks_copy` | pass |
| AC7 | `OnlyTest.test_unknown_or_disabled_harness_is_an_error_and_writes_nothing`, `test_a_broken_harnesses_file_fails_as_without_only` | pass |

## Notes
- Mutation check: `tests/test_cli_args.py` against the base `brainrc/` fails 14 of 15 tests; the one that passes (scope ends with the command) only pins cleanup.
- Two existing tests changed on purpose: `help` and `bogus` used to print usage to stdout with exit 2; now `--help` exits 0 and a bad command prints usage to stderr.
- Reviewed inline (one context), so `review_context: shared`.
