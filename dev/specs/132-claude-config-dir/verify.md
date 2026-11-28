# Verify: Read CLAUDE_CONFIG_DIR for claude

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
| AC1 | `SetTest.test_claude_config_dir_outside_home` (status, apply, status, doctor, uninstall; nothing under `~/.claude` or `~/.claude.json`) | pass |
| AC2 | `UnsetTest.test_each_harness_uses_its_default` (claude) | pass |
| AC3 | `EmptyTest.test_each_harness_uses_its_default` (claude); `EnvDirTest.test_unset_empty_or_relative_falls_back` | pass |
| AC4 | `test_claude_hook_commands_point_into_the_var`, `test_claude_config_dir_outside_home` (MCP at `$CLAUDE_CONFIG_DIR/.claude.json`), `DoctorPluginDirTest.test_doctor_reads_claude_plugins_from_the_var` | pass |
| AC5 | full suite with all three vars set to temp dirs: 0 files written there | pass |

## Notes
- Mutation check: `tests/test_harness_env.py` against the base `brainrc/` and `harnesses.toml` (new names stubbed to the old behavior): 14 of 22 tests fail; the rest pin the unset/default path and the JSONC helper.
- `.claude.json` inside `CLAUDE_CONFIG_DIR` was checked against Claude Code 2.1.322: `claude mcp add -s user` with the var set wrote `$CLAUDE_CONFIG_DIR/.claude.json`.
- The manifest's trust check now also accepts paths inside a dir a harness var names now, so uninstall doesn't warn for `CLAUDE_CONFIG_DIR` outside `~`. Format unchanged.
- Reviewed inline (one context), so `review_context: shared`; the PR goes to the code-reviewer channel too.
