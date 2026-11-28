# Spec: Owned hooks dirs, MCP ownership and backups follow the brainrc name

Ticket: gh:207 (epic #199, 4 of 6) · Size: standard · Status: approved

## Problem
After #205 and #206 the tool and its home are `brainrc`, but `apply` still names its hook dirs
`hooks/ai-config` and `hooks/ai-config-<pack>`, recognizes its own hook entries by that path, and
writes backups as `.bak-aicfg-*`. Renaming any of these naively makes `apply` treat existing
entries as the user's and add new ones beside them, so every guard hook runs twice, old links
linger, and old backups never get pruned. MCP ownership records (`mcp-owned.json`) must also
survive the rename and the home move without duplicating servers.

## Goals
- New installs use `hooks/brainrc` and `hooks/brainrc-<pack>` and `.bak-brainrc-*` backups.
- One `apply` on an old-name install converges it: no duplicates, no leftovers, status in sync.
- User-owned entries are never claimed by accident.

## Non-goals
- Plugin namespace and `.claude-plugin` names (#208); general wording, docs sweep (#209).
- Renaming MCP block markers (`# >>> ai-config mcp servers`) unless needed for ownership (see Q3).
- Removing old-name support; it stays for the deprecation window (`SHIM_REMOVED_IN`, 0.5.0).
- Touching the real HOME: every test uses a temp HOME.

## Acceptance criteria
"Old-name install" = temp HOME with hook links `~/.claude/hooks/ai-config` and
`~/.cursor/hooks/ai-config` (plus `-<pack>` links for an enabled pack), settings entries pointing
there, an MCP ownership record, and `.bak-aicfg-*` backups.

- **AC1**: Given a fresh temp HOME, when `apply` runs, then hook links are `hooks/brainrc` (and
  `hooks/brainrc-<pack>`), settings commands reference them, and no `ai-config` hook path exists.
- **AC2**: Given an old-name install, when `apply` runs once, then each guard hook appears exactly
  once in Claude `settings.json` and Cursor `hooks.json` (any other enabled harness that merges
  hooks likewise), all pointing at the new dirs.
- **AC3**: Given AC2, then the old hook links `hooks/ai-config*` are removed, and so is any copy
  they led to under the settings home that apply made. Real files or dirs the user put there stay.
- **AC4**: Given a hook entry whose command merely contains `ai-config` elsewhere (e.g.
  `~/src/ai-config/run.sh`, `/hooks/ai-configs/x`, `/hooks/my-ai-config/x`), when `apply` runs,
  then it is kept untouched and in place. Entries under `/hooks/ai-config/`, `/hooks/ai-config-<pack>/`,
  `/hooks/brainrc/`, `/hooks/brainrc-<pack>/` are owned and replaced; other tools' entries are kept.
- **AC5**: Given a disabled harness or pack whose settings still hold old-name or new-name owned
  hooks, when `apply` runs, then those entries are removed.
- **AC6**: Given an old-name install with MCP servers recorded as owned in
  `<resolved home>/mcp-owned.json`, when `apply` runs, then no server is duplicated or reported as
  a conflict, entries are updated in place, and the record is kept in the resolved home.
- **AC7**: Given the user has not migrated (record only in a former home, resolved home is the new
  one), when `apply` runs, then that record is honored the same way (read-only), the new record is
  written to the resolved home, and the former home's file is not modified. Where records differ
  for one file, the resolved home wins.
- **AC8**: Given no record anywhere and a server the user defined under the same name, then it is
  still reported as a conflict and never overwritten (unchanged behavior).
- **AC9**: Given `apply` backs up a settings or MCP file, then the backup is named
  `<file>.bak-brainrc-<UTC stamp>`; no `.bak-aicfg-*` is created.
- **AC10**: Given `.bak-aicfg-*` and `.bak-brainrc-*` backups of one file totalling more than 5,
  when `apply` writes that file, then the newest 5 by timestamp across both names remain (the new
  backup included) and the oldest are deleted first; with equal stamps the old name goes first.
  Unrelated files are never deleted.
- **AC11**: Given AC2's setup after one `apply`, then `brainrc status` reports everything in sync
  and `brainrc doctor` reports no hook or MCP finding about the old names.
- **AC12**: Given AC11, when `apply` runs a second time, then no file changes: no new backup, no
  settings or ownership write, no link change; exit 0.
- **AC13**: Given the suite, then AC1 to AC12 run on a temp HOME, and
  `python3 -m unittest discover -s tests` and `python3 scripts/brainrc.py validate` pass.

## Constraints
- Stdlib-only Python 3.11+; offline. Settings merge stays atomic, mode-preserving, symlink-safe,
  lock-guarded (living `aicfg-apply`).
- Ownership matching is by path component, not substring of the whole command.
- A hook dir the user overrides in `harnesses.local.toml` is used as given (still owned by marker).
- `docs/troubleshooting.md` (backup name) is updated only where now wrong.

## Requirement changes
### Area: aicfg-apply
#### ADDED: Owned hook dirs are renamed without duplicates
`brainrc apply` SHALL link hooks at `hooks/brainrc` and `hooks/brainrc-<pack>`, treat hook entries
under those and the former `hooks/ai-config(-<pack>)` dirs as its own, replace them with the new
ones, and remove the old links on the first apply; entries that only mention `ai-config` elsewhere
SHALL be left alone. (AC1 to AC5)
#### ADDED: MCP ownership survives the rename
`brainrc apply` SHALL honor ownership records in the resolved home and, read-only, in former homes,
so servers it wrote earlier are updated rather than duplicated or reported as conflicts. (AC6 to AC8)
#### ADDED: Backups use the brainrc name
`brainrc apply` SHALL name backups `<file>.bak-brainrc-<UTC time>` and keep the newest 5 counting
existing `.bak-aicfg-*` ones, pruning the oldest first. (AC9, AC10)
#### ADDED: Convergence
After one `apply` of an old-name install `brainrc status` SHALL report in sync and a second `apply`
SHALL change nothing. (AC11, AC12)
#### MODIFIED: Hooks fail open
brainrc's hook commands SHALL exit 0 without blocking (Cursor: with an allow response) when their
script file is missing, and behave as the guard otherwise. (Wording only; behavior unchanged.)
#### MODIFIED: Doctor checks hooks
`brainrc doctor` SHALL report each brainrc hook (new or old dir name) in a harness's settings file
whose script is missing, or that exits non-zero for an empty payload, with the fix. (AC11)
#### MODIFIED: Safe atomic writes
Unchanged except that the backup made before a write is named `.bak-brainrc-*`. (AC9)

## Open questions
1. Hook dir overridden in `harnesses.local.toml` (custom name): not renamed, only owned via its
   marker. *Matters: a user-set dir would otherwise move silently.* Default taken: leave as is.
2. Legacy match breadth: keep claiming any `/hooks/ai-config-<anything>/` (as today), so a user's own
   dir of that shape is claimed as before. *Matters: AC4 boundary.* Default taken: keep, no widening.
3. Codex MCP block markers still say `ai-config`; the block is its own record and is already found.
   *Matters: rename now or in #209.* Default taken: unchanged here; defer to #209.
4. Ticket Files list names `aicfg/`; the package is now `brainrc/`. *Matters: file paths only.*
   Default taken: use `brainrc/` modules.
5. Old-name records in a former home are never cleaned up by `apply` (only `migrate` moves them).
   *Matters: stray files.* Default taken: leave them; doctor's #206 "old dir unused" WARN covers it.

## Proposed split
Not applicable (standard).
