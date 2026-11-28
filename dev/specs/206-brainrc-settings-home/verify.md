# Verify: Settings home ~/.config/brainrc and BRAINRC_HOME

Run at 2026-10-28T04:50:21Z on commit `a45dc69`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 525 tests, OK |
| Lint | not configured | not configured |
| Build | `pip install` into a fresh venv; `scripts/check_install.py` | pass: 6/6 PASS |
| Validate (infra) | `python3 scripts/brainrc.py validate`; `--pack examples/pack-acme`; sandbox tests; `plugin` | pass: OK; pack OK; sandbox OK; manifests unchanged |
| Plan / diff | end-to-end on the installed package with a temp HOME (below) | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | tests/test_settings_home.py `test_ac1_*` | pass |
| AC2 | `test_ac2_*` (2) | pass |
| AC3 | `test_ac3_*` (6, incl. XDG + legacy-only uses legacy and warns: amended criterion) | pass |
| AC4 | `test_ac4_*` (3); e2e: legacy `apply` exit 0, one stderr line naming `brainrc migrate` | pass |
| AC5 | `test_ac5_*` (4) | pass |
| AC6 | `test_ac6_*` | pass |
| AC7 | tests/test_migrate.py `test_ac7_*` (3, incl. symlinked and relative-symlinked dirs); e2e: local rule byte-identical, 15 links re-pointed, 0 left in the old dir | pass |
| AC8 | `test_ac8_*` (2) | pass |
| AC9 | `test_ac9_*` (2); e2e: `--dry-run` exit 0, nothing moved | pass |
| AC10 | `test_ac10_*`; e2e: second `migrate` "Nothing to migrate", exit 0 | pass |
| AC11 | `test_ac11_*` (2) | pass |
| AC12 | `test_ac12_*`, TestLocks (2) | pass |
| AC13 | `test_ac13_*` | pass |
| AC14 | tests/test_doctor_home.py (7); e2e: `doctor` WARN on the legacy home, none after migrate | pass |
| AC15 | tests/test_active_run.py (7 new) | pass |
| AC16 | every case above uses a temp HOME; suite and validate pass | pass |

## Notes
- Path-safety, lock, cross-device and link re-point tests in tests/test_migrate.py (29) go beyond the criteria; each hardening test failed under a mutation reverting its fix.
- `check_install.py` and CI on the PR repeat the installed-package checks.
