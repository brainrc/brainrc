# Verify: Remove the deprecated aicfg names in 0.5.0

Run at 2026-10-29T04:10:00Z on commit `07e4537`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (also with `XDG_CONFIG_HOME=/home/runner/.config`) | pass: 593 tests, OK (1 skipped) both ways |
| Lint | not configured | not configured |
| Build | `pip install .` in a fresh venv, then `scripts/check_install.py` from outside the checkout (the CI step) | pass: every check PASS, including "no aicfg package installed" |
| Validate (infra) | `python3 scripts/brainrc.py validate`; `validate --pack examples/pack-acme` | pass |
| Sandbox | `python3 -m unittest -q` in `examples/sandbox` | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `PyprojectTest` (only the `brainrc` script and package); `test_scripts_aicfg_is_gone`, `test_python_m_aicfg_and_import_aicfg_are_gone`; check_install "no aicfg package installed"; CI step removed | pass |
| AC2 | `test_removed_names_are_gone`; `test_no_command_prints_a_deprecation_line_for_the_old_home_vars` | pass |
| AC3 | `TestAicfgHomeEnv` `test_ac3_*`: exact error, nothing written, a filled new home is not refused, `BRAINRC_HOME` wins | pass |
| AC4 | `TestLegacyHome` `test_ac4_*` and `TestXdgConfigHome` `test_ac4_absolute_xdg_with_only_legacy_dir_is_refused`. With the refusal off, 10 tests fail. | pass |
| AC5 | `test_ac5_migrate_then_apply_succeeds`, `test_ac5_migrate_with_brainrc_home_then_apply_succeeds`, `test_ac5_doctor_fails_with_the_migrate_fix`, `test_ac5_other_commands_do_not_refuse` (asserts the doctor FAIL line and its fix), `test_ac5_version_validate_and_plugin_do_not_refuse` | pass |
| AC6 | test_active_run `test_aicfg_home_is_not_read`, `test_legacy_home_is_not_read`, `test_legacy_home_is_not_read_with_xdg_set` | pass |
| AC7 | the pins read `<0.6`; `validate --pack examples/pack-acme` passes | pass |
| AC8 | `bump: minor` fragment with a [pack contract] bullet. `validate` passes with it at VERSION 0.4.5: the 236 removal-release check is off because `SHIM_REMOVED_IN` is gone. Its tests still exercise the check, with the constant patched in. | pass |
| AC9 | test_old_names passes; 22 stale rows were dropped; the new rows are narrow; check_install has no aicfg checks | pass |

## Review
code-reviewer found nothing blocking. The should-fix and nit findings, and what was done:
- The install note's reason to uninstall first was stale: reworded.
- The living specs were stale: applied.
- A doctor test assertion was vacuous: it now asserts the FAIL line and its fix.
- Left as is (matches the spec): a stale `AICFG_HOME` pointing at a missing dir refuses until it is unset; the message says to set `BRAINRC_HOME`.
- Left as is (harmless): a dangling `~/.config/ai-config` symlink is not detected.
