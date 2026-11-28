# Verify: Keep core employer-neutral, mechanically

Run at 2026-11-10T06:11Z on commit `25f23d1`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 712 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 712 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `LocalTripwireTest.test_a_term_in_a_core_file_fails_with_file_and_line`, `test_any_file_type_and_file_names_are_checked`; in the real checkout, `terms = ["Initech"]` plus a line in `docs/install.md` fails validate | pass |
| AC2 | `test_without_the_file_validate_passes`, `test_a_term_found_nowhere_passes`; `ValidateTest.test_repo_is_valid` | pass |
| AC3 | `test_in_a_git_checkout_only_tracked_files_are_checked`, `test_per_machine_local_files_are_not_checked` | pass |
| AC4 | `test_the_file_must_never_be_tracked`, `test_the_repo_ignores_the_file` (`git check-ignore`) | pass |
| AC5 | `test_bad_terms_fail_without_a_traceback` | pass |
| AC6 | AGENTS.md "Keep it generic" bullet; CONTRIBUTING.md Setup section with a `terms` example | pass |

## Notes
- Mutation check: the 9 new tests run against the base `validate.py` fail 5; the 4 that pass pin behavior that must not change (no file, no hits, `.gitignore`).
- The pre-commit config is unchanged: its `brainrc-validate` hook already runs `validate` on every commit, which now reads the local file.
- Reviewed inline (one context), so `review_context: shared`.
