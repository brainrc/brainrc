# Verify: Reserved skill names check in validate

Spec: [spec.md](spec.md) · Commit: 8a2e170

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 771 ran, OK (1 skipped) |
| Validate | `python3 scripts/brainrc.py validate` | pass: OK, 32 skills, 10 agents |
| Targeted | `python3 -m unittest tests.test_reserved_names` | pass: 5 OK |
| Mutation | exemption forced off in validate.py | 3 failures, as expected (reverted) |
| Secret scan | gitleaks 8.24.3 over `149-1-namespaced-skills..HEAD` | pass: no leaks |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_reserved_core_skill_fails_naming_it` (init, help, status, compact) | pass |
| AC2 | `test_shipped_tree_passes`, `test_declared_aliases_are_exempt`, `test_pack_skill_is_not_checked_for_reserved_names` | pass |
| AC3 | `test_core_and_pack_duplicate_still_reported` (validate path) and existing `test_name_collision_writes_nothing` (sync path) | pass |

## Notes
- The reserved list is the parent spec's Q1 default, not checked against each harness.
