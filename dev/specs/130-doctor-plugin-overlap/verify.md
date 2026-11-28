# Verify: Doctor detects double installs

Run at 2026-11-10T17:36Z on commit `c3ed729`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 805 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 805 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `DoubleInstallTest.test_claude_plugin_and_links_warn_and_name_what_to_remove`, `test_a_plugin_from_another_marketplace_counts`, `DoubleInstallDoctorTest.test_doctor_warns_after_apply_and_not_before` | pass |
| AC2 | `DoubleInstallTest.test_cursor_plugin_and_links_warn` | pass |
| AC3 | `test_no_warning_without_both`, `test_a_disabled_plugin_does_not_warn`, `TestPluginFindings.test_warnings_do_not_change_exit_code` | pass |
