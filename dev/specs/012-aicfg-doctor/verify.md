# Verify: `aicfg doctor`

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_writes_nothing`: snapshot of HOME and repo (link targets, sizes, mtimes) identical after doctor finds 3 problems | pass |
| AC2 | `test_stale_render`, `test_missing_render`; real run on this machine reports both renders as not rendered | pass |
| AC3 | `test_missing_link`, `test_many_missing_links_are_one_line`, `test_link_to_the_wrong_item`, `test_stale_link`, `test_broken_link_after_moving_the_repo`, `test_real_file_where_a_link_belongs` | pass |
| AC4 | `test_harness_not_installed_warns` (only finding is a WARN, exit 0, fix names `harnesses.local.toml`); real run warns for codex, opencode, gemini, cursor | pass |
| AC5 | `test_missing_pack_path` (one FAIL, other checks still clean), `test_incompatible_pack` | pass |
| AC6 | `test_unmerged_hooks`, `test_invalid_settings_json`; real run reports unmerged `~/.claude/settings.json` | pass |
| AC7 | `PythonVersionTest`: with `tomllib` hidden, exit 1 and "needs Python 3.11+" on stderr, no traceback | pass |
| AC8 | `FAIL`/`WARN` line plus `fix:` line per finding, summary, exit codes asserted in every DoctorTest case; `No problems found.` in `test_clean_after_apply` | pass |
| AC9 | module docstring usage (`aicfg.py help`), README Install section and layout line, VERSION 0.3.7, CHANGELOG 0.3.7; `validate` OK | pass |

## Commands
- `python3 -m unittest discover -s tests -q` → OK (16 new tests)
- `python3 scripts/aicfg.py validate` → OK: 21 skills, 9 agents, 5 commands
- `python3 scripts/aicfg.py validate --pack examples/pack-acme` → OK
- `python3 scripts/aicfg.py doctor` on this machine → 4 problems, 4 warnings, exit 1 (never applied here)

## Changes from the plan
- Missing links are grouped into one line per harness when there are more than 3, after the
  real run printed 37 identical lines for a never-applied harness. Test added (red first).
- `plan()` takes an optional `every_src`, so a broken pack doesn't make doctor raise.
