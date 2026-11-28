Lock aicfg apply and skip files that change mid-apply

2 of 4 in epic #92 (E1: Safe writes and fail-open hooks).

## Why
Two `aicfg apply` runs at once overwrote each other's merges, and both used the same temp file name. Claude Code rewrites `~/.claude.json` while it runs, so a write that landed between apply's read and its rename was silently thrown away.

## What changed
- `apply` takes a non-blocking exclusive lock on `$AICFG_HOME/apply.lock` (`fcntl.flock`, `msvcrt` on Windows). If another run holds it, apply prints `ERROR another aicfg apply is running (lock: <path>)` and exits 1 before writing anything. The OS releases the lock when the process exits. `status` takes no lock.
- Before replacing a settings or MCP file, `replace_file` re-reads it. If the file changed since apply read it, apply leaves it alone, prints `CHANGED … (changed during apply; close Claude Code and re-run)`, and exits 1. Other files are still written.
- Temp files are named `.<name>.aicfg-tmp-<pid>`.
- `docs/troubleshooting.md` has a new section, "Apply while something else writes".

## Acceptance criteria
- [x] AC1: a second apply exits 1 without writing, verified by `test_a_second_apply_fails_while_one_holds_the_lock` and a real two-process run
- [x] AC2: the lock is released after a normal run and after an exception, verified by `test_the_lock_is_released_after_apply_even_on_error`
- [x] AC3: the temp name includes the pid and no temp file is left, verified by `test_temp_name_includes_the_pid` and `test_backups_are_capped`
- [x] AC4: a file changed mid-apply is skipped with a warning, verified by `test_settings_changed_during_apply_are_left_alone` and `test_a_claude_json_changed_during_apply_is_left_alone`
- [x] AC5: `status` runs while the lock is held, verified by the AC1 test
- [x] AC6: the troubleshooting doc covers closing Claude Code and both messages

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- The check runs before the backup and the temp-file write, so a harness write that lands in those few milliseconds is still lost. The docs say to close Claude Code first.
- `aicfg update` fetches packs before it takes the lock.
- The `msvcrt` lock path isn't covered by tests, because the lock tests skip on Windows.

Spec: `specs/097-apply-lock-unique-tmp/spec.md` · Plan: `specs/097-apply-lock-unique-tmp/plan.md`
Closes #97
