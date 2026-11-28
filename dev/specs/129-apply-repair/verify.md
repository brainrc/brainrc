# Verify: apply --repair for a moved checkout

Run at 2026-11-10T17:32Z on commit `3a497ca`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 799 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 799 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme` | pass: both OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `RepairTest.test_a_moved_checkout_is_back_in_sync_after_repair` | pass |
| AC2 | `test_a_moved_checkout_is_back_in_sync_after_repair`, `test_repair_works_without_a_manifest` | pass |
| AC3 | `test_an_item_gone_from_the_moved_checkout_is_pruned`, `test_repair_works_without_a_manifest` | pass |
| AC4 | `test_a_broken_link_to_another_item_stays_a_conflict`, `test_a_working_link_to_the_users_own_copy_stays_a_conflict` | pass |
| AC5 | `test_status_repair_writes_nothing`, `test_repair_with_only_touches_that_harness` | pass |
| AC6 | `test_a_moved_checkout_is_back_in_sync_after_repair` (hint), `test_doctor_suggests_repair_for_a_moved_checkout`, `DoctorTest.test_broken_link_after_moving_the_repo`, `DoctorTest.test_broken_link_to_another_item` | pass |

## Notes
The ticket's done-when ("move the checkout, run apply --repair → in sync") is AC1.
