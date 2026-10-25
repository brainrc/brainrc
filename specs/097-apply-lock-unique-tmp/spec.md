# Spec: Lock apply and use unique tmp names

Ticket: gh:97 · Size: standard · Status: draft

## Problem
Two `aicfg apply` runs at once (two terminals, a shell hook plus a manual run) read the same
settings and MCP files, merge, and write over each other. Both also use the same temp name
(`.<name>.aicfg-tmp`), so one run can rename the other's half-written temp file into place.
Separately, Claude Code rewrites `~/.claude.json` while it runs: if it writes between apply's
read and apply's rename, apply silently throws that write away (the user's project history,
auth state, or settings changed in the app).

## Goals
- Only one `aicfg apply` writes at a time; a second one says so clearly.
- Temp names can't collide between processes.
- Apply never silently overwrites an MCP or settings file that changed after apply read it, and
  tells the user to close Claude Code before MCP changes.

## Non-goals
- Locking `aicfg status`, `validate`, or `doctor` (read-only).
- Locking pack fetches in `aicfg update` beyond the apply it runs.
- Closing the last tiny window between the final check and the rename (impossible without the
  harness's cooperation); the docs cover it.
- Cleaning up temp files left by crashed runs of other processes.

## Acceptance criteria
- **AC1**: Given an `aicfg apply` is running and holds the apply lock, when a second
  `aicfg apply` starts, then the second exits non-zero without writing anything and prints that
  another apply is running, naming the lock file.
- **AC2**: Given no other apply is running, when `aicfg apply` finishes (or fails with an
  exception), then the lock is released and the next apply runs normally.
- **AC3**: Given `aicfg apply` writes a settings or MCP file, when it creates the temp file, then
  the temp file's name includes the process id, and no temp file is left after the write.
- **AC4**: Given apply has read an MCP or settings file, when that file's content changes before
  apply writes it (a running Claude Code), then apply does not write that file, prints a warning
  naming the file and saying to close Claude Code and re-run, and exits non-zero; other files are
  still written.
- **AC5**: Given `aicfg status` (dry run), when it runs while an apply holds the lock, then it
  runs normally (no lock taken).
- **AC6**: Given the troubleshooting doc, when a user reads it, then it says to close Claude Code
  before MCP changes and explains the "another apply is running" and "changed during apply"
  messages.

## Constraints
- Stdlib only. POSIX (macOS, Linux) required; Windows must not crash (lock may degrade).
- The lock must not outlive a killed process (no stale-lock manual cleanup).
- Builds on gh:96's `replace_file`.

## Requirement changes

### Area: aicfg-apply
#### ADDED: One apply at a time
`aicfg apply` SHALL hold an exclusive lock while it writes, and a second apply SHALL exit
non-zero with a clear message instead of writing. Read-only commands SHALL NOT take the lock.
(AC1, AC2, AC5)
#### ADDED: No lost concurrent writes
`aicfg apply` SHALL use per-process temp names, and SHALL NOT overwrite a settings or MCP file
whose content changed after apply read it; it warns and exits non-zero instead. (AC3, AC4)

## Open questions
1. Second apply: **fail fast** (analyst default, AC1) or wait for the lock (with a timeout)?
   *Matters for scripted applies (a shell hook), which would rather wait.* Fail fast is simpler
   and the message tells the user what to do.
2. File changed during apply: **skip it and exit non-zero** (default, AC4), or re-read and
   re-merge once? *Re-merging recovers automatically, but can loop against a harness that writes
   constantly; skipping is predictable.*
