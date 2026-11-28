# Verify: Read XDG_CONFIG_HOME for opencode

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
| AC1 | `SetTest.test_opencode_xdg_config_home` | pass |
| AC2 | `UnsetTest.test_each_harness_uses_its_default` (opencode) | pass |
| AC3 | `EmptyTest.test_each_harness_uses_its_default` (opencode) | pass |
| AC4 | `OpencodeJsoncTest.test_an_existing_jsonc_is_merged_and_keeps_comments`, `test_jsonc_under_xdg`, `test_json_wins_when_both_exist`, `test_only_opencode_looks_for_jsonc`; `JsoncTest` | pass |
| AC5 | `OpencodeJsoncTest.test_a_jsonc_it_cant_parse_is_left_alone`, `JsoncTest.test_rejects_what_isnt_an_object` | pass |

## Notes
- Mutation check: `tests/test_harness_env.py` against the base `brainrc/` and `harnesses.toml` (new names stubbed to the old behavior): 14 of 22 tests fail; the rest pin the unset/default path and the JSONC helper.
- The JSONC edit replaces only the `mcp` key and is re-parsed before it is written; a mismatch leaves the file alone (`invalid`).
- `specs/013-tutorial/run-tutorial.sh` failed on main too (its temp HOME had no harness after #126); it now creates `~/.claude` like `check_tutorial.py` does.
- Reviewed inline (one context), so `review_context: shared`; the PR goes to the code-reviewer channel too.
