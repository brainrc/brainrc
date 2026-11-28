# Verify: validate enforces the pack naming rules

Run at 2026-11-11T07:10:00Z on the epic branch.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 940 ran, 0 failed, 1 skipped |
| Validate | `brainrc.py validate`; `--pack examples/pack-acme`; `--pack examples/pack-homelab` | pass |
| Tutorial | `python3 scripts/check_tutorial.py` | pass |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `ReservedTest`, `ValidateTest.test_a_reserved_prefix_fails_validate` | pass |
| AC2 | `OwnerPrefixTest` | pass |
| AC3 | `VendorTest` | pass |
| AC4 | `LookalikeTest` | pass |
| AC5 | `CharsetTest` | pass |
| AC6 | `PrefixLengthTest` | pass |
| AC7 | `ValidateTest.test_examples_pass`, `test_docs_list_the_same_official_ids`; core validate | pass |
