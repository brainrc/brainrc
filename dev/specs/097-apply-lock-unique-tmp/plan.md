# Plan: Lock apply and use unique tmp names

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none (stdlib `fcntl`, `msvcrt` on Windows)
- **Public API / contract changes:** none for users. Internal: `replace_file`, `write_settings`,
  and `write_mcp` gain a required `before` argument; their only callers are `cli.py`.
- **Migrations / data changes:** none. New file `$AICFG_HOME/apply.lock` (empty, left in place).
- **Security triggers touched:** none new. Concurrency in writes to `~/.claude.json` (data loss).
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
**Changed-during-apply guard.** `cli.cmd_sync` reads each settings or MCP file's text right before
it computes the change (`read_current(path) -> str | None`, new in `aicfg/settings.py`; `None`
when absent). It passes that `before` to `write_settings` / `write_mcp`, which pass it to
`replace_file`. Just before backing up, `replace_file` re-reads the target. If the text differs
from `before` (or the file appeared or vanished), it raises `FileChanged` and writes nothing.
`cli` catches it, prints `CHANGED <harness> <path>  (changed during apply; close Claude Code
and re-run)`, counts it as a conflict (so the exit is non-zero) and continues with other files.
`record_owned` runs only after a successful write. `settings_change` and `mcp_change` keep their
signatures, so `doctor.py` is untouched; a change between `cli`'s read and theirs is caught too
(a harmless false positive).

**Unique temp names.** `replace_file` names the temp `.<name>.aicfg-tmp-<pid>`.

**Lock.** `cmd_sync(apply=True)` runs the current body (renamed `_sync`) inside `apply_lock()`,
a context manager in `cli.py`: open `$AICFG_HOME/apply.lock` (mkdir parents) and take a
non-blocking exclusive `fcntl.flock` (`msvcrt.locking(LK_NBLCK)` on Windows). The kernel drops
the lock when the process dies, so there is no stale lock. When it's held: print
`ERROR another aicfg apply is running (lock: <path>)` and return 1 before writing anything.
`status` calls `_sync(False)` with no lock. `cmd_update` gets the lock through `cmd_sync`.

Design choice: read `before` in `cli` rather than widening `settings_change`/`mcp_change`, so
their return shapes (used by `doctor`) stay as they are.

## Files
| File | Change |
|---|---|
| `aicfg/settings.py` | `read_current`, `FileChanged`; `replace_file(dest, text, before)` checks and uses pid temp names; `write_settings` passes `before` |
| `aicfg/mcp.py` | `write_mcp(m, text, owned, before)` |
| `aicfg/cli.py` | read `before`, catch `FileChanged`; `apply_lock()`, `_sync` |
| `tests/test_aicfg.py` | changed-settings test, pid temp name, lock held / released / status unlocked |
| `tests/test_mcp.py` | changed `~/.claude.json` is skipped, other harness files still written |
| `docs/troubleshooting.md` | close Claude Code first; the two new messages |

## Risks
- Tests that patch around temp names (`.settings.json.aicfg-tmp` glob in `test_backups_are_capped`)
  need the new pattern; update the assertion, not weaken it.
- AC4 needs a change between read and write inside one run: the test patches `settings_change`
  / `mcp_change` (via `aicfg.cli`) to modify the file after the real call returns.

## Test strategy
Integration through `aicfg.cmd_sync` with a fake HOME, as existing tests do. AC1 holds the lock
from the test with `fcntl.flock` on the same path (separate open file → conflicts, even in-process).
AC2 runs apply twice, and once with a forced exception, then applies again. AC5 runs status
while the test holds the lock. AC6 is a doc check by the verifier.

## Tasks
- [ ] **T1** [agent: implementer] Changed-during-apply guard and pid temp names
  - files: `aicfg/settings.py`, `aicfg/mcp.py`, `aicfg/cli.py`, `tests/test_aicfg.py`, `tests/test_mcp.py`
  - criteria: AC3, AC4
  - review: each
- [ ] **T2** [agent: implementer] Apply lock
  - files: `aicfg/cli.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC5
  - after: T1
- [ ] **T3** [agent: implementer] Troubleshooting docs for the lock and changed-file messages
  - files: `docs/troubleshooting.md`
  - criteria: AC6
  - after: T2
