Record the active run's path for external tools

## Why
Tools that look for the current run in `<cwd>/specs/` find nothing when the session starts in another directory, such as a pack repo or a workspace root. The run's path now goes in one file outside the repo that those tools can read.

## What changed
- spec-agent writes the run's absolute path to `$AICFG_HOME/active-run` (default `~/.config/ai-config/active-run`) at intake, on resume, and at every checkpoint commit. Nothing clears it, so a finished run stays named until the next one starts.
- New `skills/spec-agent/scripts/active_run.py write|read`. `read` falls back to the newest `<cwd>/specs/*/state.json` when the pointer is missing or names no directory. A failed write warns on stderr, and the run continues.
- The file contract is `references/state.md` § Active run pointer. `docs/spec-agent.md` links to it.
- Adds the `run-pointer` living spec (new area, three requirements).
- Blast radius: one file under `$AICFG_HOME`, written at each run step. No repo file is deleted or moved. Rollback: revert. A leftover pointer keeps naming the last run until it is deleted.

## Acceptance criteria
AC4 to AC7 and AC12 describe agent behavior in the docs. They are checked by reading the docs, not by running them.
- [x] AC1: write from another directory records the absolute run path. `test_write_from_other_directory_records_absolute_run_path`
- [x] AC2: unset `AICFG_HOME` uses `~/.config/ai-config`. `test_write_defaults_to_dot_config_ai_config_when_env_unset`
- [x] AC3: file is `path\n` and nothing else. `test_pointer_is_single_line_path_plus_newline_only`
- [x] AC4: intake writes the pointer (`lifecycle.md` step 5). Doc check.
- [x] AC5: a new write replaces another run's path. `test_write_replaces_another_runs_pointer`. Resume step in `state.md`.
- [x] AC6: every checkpoint commit writes the pointer (`state.md`). Doc check.
- [x] AC7: nothing clears the pointer, and the script has no clear command. Doc check.
- [x] AC8: missing `AICFG_HOME` directory is created. `test_write_creates_missing_aicfg_home_directory`
- [x] AC9: `write` and `read` subcommands. `test_read_prints_pointer_run_when_directory_exists`
- [x] AC10: fallback to `<cwd>/specs/` by `state.json` mtime. Five `test_read_*` fallback tests.
- [x] AC11: unwritable home warns and exits 0. `test_write_warns_and_exits_zero_*` (two tests).
- [x] AC12: `state.md` documents location, format, write moments, persistence, and fallback. Doc check.

## How to verify
```
python3 -m unittest discover -s tests -p test_active_run.py -v
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- `write` does not check that the run directory exists. A wrong path is recorded silently, and `read` then falls back.
- The `RuntimeError` catch in `write` and `read` (no `HOME` or passwd entry) has no test.
- `write` leaks the file descriptor if `os.fdopen` fails. LOW, not fixed.
- The agent-orchestration mod, outside this repo, still has to read the pointer (item 4 of gh:71).

Spec: `specs/071-active-run-pointer/spec.md` · Plan: `specs/071-active-run-pointer/plan.md`
Refs #71

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01BdiJDGmXUuJTx5qC4ADnaF
