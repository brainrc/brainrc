# aicfg-apply

How `aicfg apply` writes harness settings and MCP config files.

### Safe atomic writes
Unchanged except that the backup made before a write is named `.bak-brainrc-*`. (AC9)
_Last changed by 207-brainrc-hooks-mcp-backups._

### Symlinked config files
When a settings or MCP file path is a symlink, `brainrc apply` SHALL write through to the link's final target (creating it if the link dangles), keep the link, and back up the target's previous content. (AC3, AC4, AC6, AC7)
_Last changed by 209-brainrc-docs-wording._

### One apply at a time
`brainrc apply` SHALL hold an exclusive lock while it writes, and a second apply SHALL exit non-zero with a clear message instead of writing. Read-only commands SHALL NOT take the lock. (AC1, AC2, AC5)
_Last changed by 209-brainrc-docs-wording._

### No lost concurrent writes
`brainrc apply` SHALL use per-process temp names, and SHALL NOT overwrite a settings or MCP file whose content changed after apply read it; it warns and exits non-zero instead. (AC3, AC4)
_Last changed by 209-brainrc-docs-wording._

### Hooks fail open
brainrc's hook commands SHALL exit 0 without blocking (Cursor: with an allow response) when their
script file is missing, and behave as the guard otherwise. (Wording only; behavior unchanged.)
_Last changed by 207-brainrc-hooks-mcp-backups._

### Doctor checks hooks
`brainrc doctor` SHALL report each brainrc hook (new or old dir name) in a harness's settings file
whose script is missing, or that exits non-zero for an empty payload, with the fix. (AC11)
_Last changed by 207-brainrc-hooks-mcp-backups._

### Installed hooks live in AICFG_HOME
When `brainrc` runs from an installed package, `brainrc apply` SHALL copy core's hooks to
`<settings home>/hooks/core/<harness>/hooks/` and link `hooks_dir` there, refresh the copy when
the package's hooks change, and remove it when no harness with hooks is enabled. From a checkout,
hooks SHALL stay linked into the checkout. (AC1, AC7)
_Last changed by 206-brainrc-settings-home._

### Doctor reports an unmigrated home
`brainrc doctor` SHALL warn, with the fix, when the legacy dir or `AICFG_HOME` is in use or an
unused old dir remains. (AC14)
_Last changed by 206-brainrc-settings-home._

### Owned hook dirs are renamed without duplicates
`brainrc apply` SHALL link hooks at `hooks/brainrc` and `hooks/brainrc-<pack>`, treat hook entries
under those and the former `hooks/ai-config(-<pack>)` dirs as its own, replace them with the new
ones, and remove the old links on the first apply; entries that only mention `ai-config` elsewhere
SHALL be left alone. (AC1 to AC5)
_Last changed by 207-brainrc-hooks-mcp-backups._

### MCP ownership survives the rename
`brainrc apply` SHALL honor ownership records in the resolved home and, read-only, in former homes,
so servers it wrote earlier are updated rather than duplicated or reported as conflicts. (AC6 to AC8)
_Last changed by 207-brainrc-hooks-mcp-backups._

### Backups use the brainrc name
`brainrc apply` SHALL name backups `<file>.bak-brainrc-<UTC time>` and keep the newest 5 counting
existing `.bak-aicfg-*` ones, pruning the oldest first. (AC9, AC10)
_Last changed by 207-brainrc-hooks-mcp-backups._

### Convergence
After one `apply` of an old-name install `brainrc status` SHALL report in sync and a second `apply`
SHALL change nothing. (AC11, AC12)
_Last changed by 207-brainrc-hooks-mcp-backups._
