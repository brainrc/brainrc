# Verify: Fix doc drift

Run at 2026-11-10T06:18Z on commit `26230a5`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 720 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 720 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `docs/install.md` "Stay on a release" line: `git checkout v<X.Y.Z>` with a Releases link | pass |
| AC2 | `DocVersionTest.test_install_docs_pin_the_current_minor_or_a_placeholder` (fails on the base `docs/install.md`, naming `git checkout v0.3.29`), `test_a_stale_pin_is_found`, `test_placeholders_and_history_are_not_pins` | pass |
| AC3 | `overrides/README.md`: Claude Code and Cursor hooks and fragments, OpenCode `plugin.js`; matches `harnesses.toml` keys (`hooks_dir`, `settings`, `plugin`) | pass |
| AC4 | AGENTS.md line 3 and README "Treat this repo as public" | pass |
| AC5 | `ShellPathTest` (round-trip through `sh`), `DoctorFixQuotingTest.test_broken_link_fix_quotes_the_link`, `TestHomeFindings.test_unused_old_home_fix_quotes_the_dir` | pass |

## Notes
- Mutation check: with `shell_path` stubbed to `tilde` on the base `doctor.py`, 4 of the 5 new doctor tests fail on assertions.
- One retry: `OldNamesTest` flagged `AICFG_HOME` in a new test file; the test moved to the allow-listed `test_doctor_home.py`.
- Reviewed inline (one context), so `review_context: shared`.
