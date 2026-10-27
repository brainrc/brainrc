# Spec: Readable config errors

Ticket: gh:100 · Size: standard · Status: approved

## Problem
A user who edits `harnesses.toml`, `packs.toml`, their `.local.toml` overrides, or a pack's
`pack.toml` gets a Python traceback for a syntax error, a `TypeError` for a value in the wrong
place (`claude = false`), and no complaint at all for a wrong type (`enabled = "false"` counts
as enabled) or a typo (`[cursr]`, `enabeld = false`). They can't tell what's wrong or where, and
a silent typo means config they think is off stays on. `aicfg doctor | head` also crashes with a
`BrokenPipeError` traceback.

## Goals
- Every bad config value or syntax error names the file and line, says what's wrong, and stops.
- Typos in table and key names are reported instead of ignored.
- Piping any aicfg command into a pager or `head` exits quietly.

## Non-goals
- `mcp/servers.toml` and `tripwires.toml` checks (they already report their own errors).
- Checking the values of `pack.toml` beyond TOML syntax and the types of `name` and `prefix`;
  unknown `pack.toml` keys (packs carry an open `extensions` table).
- Checking that configured paths exist (doctor already does).
- Duplicate pack names (#101), pack content checks in apply (#102).

## Acceptance criteria
- **AC1**: Given a TOML syntax error in `harnesses.toml`, `harnesses.local.toml`, `packs.toml`,
  `packs.local.toml`, or a pack's `pack.toml`, when `status`, `apply`, `validate`, or `doctor`
  runs, then it prints `ERROR <file>:<line>: <what>` (file shown with `~`), prints no traceback,
  writes nothing, and exits 1 (doctor: reports it as a FAIL line with file and line, exits 1).
- **AC2**: Given `claude = false` (a top-level non-table value) in `harnesses.local.toml`, when
  any of those commands runs, then it prints `ERROR harnesses.local.toml:<line>: ...` saying a
  table `[claude]` was expected, and exits 1.
- **AC3**: Given `enabled = "false"` (or any non-boolean) under a harness or pack table, when any
  of those commands runs, then it prints `ERROR <file>:<line>: `enabled` must be true or false`
  and exits 1. Path keys (`skills`, `agents`, `commands`, `plugin`, `instructions`,
  `hooks_dir`, `settings`, `mcp`, `path`, `git`, `ref`, `agents_format`) that aren't strings fail the same way.
- **AC4**: Given an unknown key in a harness table (`enabeld = false`) or a pack table, when any
  of those commands runs, then it prints `WARN <file>:<line>: unknown key `enabeld` in [<table>]`
  and continues; the exit code is not changed by the warning.
- **AC5**: Given a table in `harnesses.local.toml` that `harnesses.toml` doesn't define
  (`[cursr]`), when any of those commands runs, then it prints
  `WARN harnesses.local.toml:<line>: unknown harness [cursr]` and continues.
- **AC6**: Given a pack's `pack.toml` whose `name` or `prefix` is not a string, when any of those
  commands runs, then it prints `ERROR <pack.toml path>:<line>: ...` and exits 1.
- **AC7**: Given any aicfg command whose stdout is closed early (`aicfg doctor | head -1`), then
  it exits without a traceback on stderr.
- **AC8**: Given the shipped `harnesses.toml` and `packs.toml` and no local files, when
  `validate` and `status` run, then they print no new WARN or ERROR lines.

## Constraints
- Python 3.11+ stdlib only (`tomllib` gives a line for syntax errors, none for values).
- Existing valid configs keep working unchanged.

## Requirement changes

### Area: aicfg-config
Purpose: How aicfg reads and checks its own config files.
#### ADDED: Readable config errors
aicfg SHALL report a TOML syntax error, a non-table top-level value, or a wrongly typed known key
in `harnesses.toml`, `packs.toml`, their `.local.toml` overrides, or a pack's `pack.toml` as
`ERROR <file>:<line>: <what>`, with no traceback, and exit 1 without writing. (AC1, AC2, AC3, AC6)
#### ADDED: Unknown config names warn
aicfg SHALL warn with file and line about an unknown key in a harness or pack table and about a
harness table defined only in `harnesses.local.toml`, and continue. (AC4, AC5, AC8)
#### ADDED: Closed output
aicfg SHALL exit without a traceback when its stdout is closed early. (AC7)

## Open questions
1. A harness defined only in `harnesses.local.toml` (AC5): keep loading it after the warning
   (today's behavior, lets a user add a harness locally) or skip it? *Skipping breaks anyone who
   added a harness that way; keeping it means a typo'd table still creates a harness with only
   the keys it sets.* Resolved at the Spec gate: keep loading it, warn only.
2. Exit code for AC7: 0, or the conventional 141 / 1? *Scripts that check `$?` after a pipe see
   it, e.g. with `set -o pipefail`.* Default: exit 0 quietly, since the reader chose to stop. Resolved at the Spec gate: exit 0.
