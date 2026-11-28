Rename the owned hooks dir and backups to brainrc

## Why
`apply` recognizes its own hook entries by the `hooks/ai-config(-<pack>)` path and its MCP servers
by `mcp-owned.json`. Renaming the hooks dir in one step would make apply treat old entries as the
user's and add new ones beside them, so every guard hook would run twice. 4 of 6 in epic #199
(rename to brainrc), after #232.

## What changed
- **[pack contract]** Hook links are `hooks/brainrc` and `hooks/brainrc-<pack>` (Claude Code and
  Cursor). Packs using `{{hooks_dir}}` need no change; hard-coded `hooks/ai-config` paths do.
- Ownership matches both names as whole path components, so one `apply` on an old install replaces
  old settings and `hooks.json` entries (each hook once) and removes the old `hooks/ai-config*`
  links: only symlinks into targets apply manages. Real files, user hooks whose path merely contains
  `ai-config`, and siblings of a `hooks_dir` the user set are left alone.
- MCP ownership records left in a former settings home (`~/.config/ai-config`, before
  `brainrc migrate`) are honored read-only. Per file the resolved home's record wins, and a stale
  former record can't claim a server the user adds later. A corrupt record claims nothing.
- Backups are `<file>.bak-brainrc-<UTC stamp>`. The 5 kept count older `.bak-aicfg-*` backups,
  ordered by stamp. Only files named exactly like a backup are pruned, never symlinks or look-alikes.

## Acceptance criteria
- [x] AC1: fresh install links `hooks/brainrc(-<pack>)`, verified by `HookDirRenameTest`
- [x] AC2: one apply on an old install gives each hook once in settings.json and hooks.json, verified by `tests/test_rename_converge.py`
- [x] AC3: old hook links removed, real files kept, the resolved home's hooks copy reused, verified by `HookDirRenameTest` and `test_rename_converge`
- [x] AC4: entries that merely contain `ai-config` aren't claimed, verified by `tests/test_ownership.py`
- [x] AC5: a disabled pack's old-name dir is pruned, verified by `HookDirRenameTest`
- [x] AC6-AC8: MCP records in the resolved and former homes, resolved wins, `[]` shadow, corrupt record, verified by `tests/test_mcp.py` and `test_rename_converge`
- [x] AC9-AC10: backup name and pruning across both names, verified by `tests/test_backups.py`
- [x] AC11-AC12: status in sync and a second apply changes nothing, verified by `test_rename_converge`
- [x] AC13: all on a temp HOME; 556 tests and `validate` pass, also with `XDG_CONFIG_HOME` set as on CI

## How to verify
```
python3 -m unittest discover -s tests
XDG_CONFIG_HOME=/home/runner/.config python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
```

## Decisions made without you
- Gates auto-approved: Spec, Deliver; see `specs/207-brainrc-hooks-mcp-backups/log.md`. The Plan
  gate stopped on its callouts (contract, data, destructive) and you approved it ("Approve continue auto").
- A `hooks_dir` set in `harnesses.local.toml` is used as given; its siblings aren't renamed or pruned.
- Legacy matching keeps today's breadth for `hooks/ai-config-<anything>`, with no widening.
- Codex MCP block markers still say `ai-config` (the block is its own record); #209 renames the wording.
- MCP records in a former home are never cleaned up by `apply`; `brainrc migrate` moves them, and
  `doctor`'s unused-old-dir warning covers what's left.
- Security trigger touched (ownership matching decides what apply deletes): the security review
  found no CRITICAL or HIGH. Its MEDIUM (loose backup glob) is fixed in this PR.
- Ticket comment not posted: `specs/207-brainrc-hooks-mcp-backups/ticket-comment.md`

## Follow-ups
- Pack names aren't validated as lowercase, so a pack named `Acme` gets `hooks/ai-config-Acme/`,
  which the ownership pattern doesn't match as an old entry (pre-existing).
- The ownership pattern is a substring match, so a user's own `…/hooks/brainrc-mytools/x.sh` is
  treated as owned (the old pattern had the same flaw). It could be anchored to the resolved hooks dirs.
- `HookDirRenameTest` inherits `PackSyncTest`, so 12 tests run twice.

Spec: `specs/207-brainrc-hooks-mcp-backups/spec.md` · Plan: `specs/207-brainrc-hooks-mcp-backups/plan.md`
Closes #207
