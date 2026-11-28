# Verify: core agents under brainrc-

Run at 2026-11-11T07:35:00Z on the epic branch, after all three members.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 950 ran, 0 failed, 1 skipped |
| Validate | `brainrc.py validate`; `--pack examples/pack-acme` | pass |
| Tutorial | `scripts/check_tutorial.py`; `specs/013-tutorial/run-tutorial.sh` | pass |
| Tokens | `brainrc.py tokens` | core 2865 / 3000 always-loaded |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `ShippedTreeTest.test_every_core_agent_is_prefixed_or_a_declared_alias`, `test_spec_agent_dispatches_the_new_names` | pass |
| AC2 | `ShippedTreeTest.test_each_alias_is_a_short_stub_that_runs_as_its_target` | pass |
| AC3 | `AliasNearMissTest` (missing, tools, body, description, unprefixed vs prefixed new agent) | pass |
| AC4 | `AliasNearMissTest.test_a_pack_may_still_name_an_old_reviewer` | pass |

## Notes
- Reviewed inline (one context), so `review_context: shared`; the PR goes to the code-reviewer channel too.
