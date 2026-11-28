# Verify: Read CODEX_HOME for codex

Run at 2026-11-11T05:20:00Z on the epic branch, after all three members.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 903 ran, 0 failed, 1 skipped |
| Tests (vars set) | `XDG_CONFIG_HOME=<tmp> CLAUDE_CONFIG_DIR=<tmp> CODEX_HOME=<tmp> python3 -m unittest discover -s tests` | pass: 903 ran; 0 files written under the three dirs |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-acme`; `scripts/check_tutorial.py`; `specs/013-tutorial/run-tutorial.sh` | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `SetTest.test_codex_home_under_home` | pass |
| AC2 | `UnsetTest.test_each_harness_uses_its_default` (codex) | pass |
| AC3 | `EmptyTest.test_each_harness_uses_its_default` (codex), `RelativeTest.test_a_relative_value_is_ignored` | pass |
| AC4 | `SetTest.test_codex_manifest_records_the_resolved_path` | pass |

## Notes
- Mutation check: `tests/test_harness_env.py` against the base `brainrc/` and `harnesses.toml` (new names stubbed to the old behavior): 14 of 22 tests fail; the rest pin the unset/default path and the JSONC helper.
- harnesses.toml lines only; the resolver came with gh:132.
- Reviewed inline (one context), so `review_context: shared`; the PR goes to the code-reviewer channel too.
