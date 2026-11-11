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
`brainrc doctor` SHALL report a FAIL, with the migrate fix, when the legacy dir or `AICFG_HOME` holds an
unmigrated home, and SHALL warn when an unused old dir remains. (AC5)
_Last changed by 238-remove-deprecated-names._

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

### Old on-disk names converge
`brainrc apply` SHALL write the brainrc Codex markers, OpenCode guard link and fetch record, and SHALL recognize and replace the old ai-config ones on the next apply without duplicating them. (AC1, AC2, AC3, AC4)
_Last changed by 237-rename-on-disk-names._

### Only installed harnesses
`brainrc apply` and `status` SHALL manage an enabled harness only when its home directory exists (the `home` key, else the parent of its `instructions` or `skills` path) or harnesses.local.toml enables it explicitly or defines it; they SHALL name each skipped harness, and SHALL never create a skipped harness's files. (AC1, AC2, AC3, AC4, AC5)
_Last changed by 126-installed-harnesses._

### Harness manifest
`brainrc apply` SHALL write `<settings home>/harnesses.json` listing each managed harness's paths and the source roots it linked from, keeping entries outside `--only` and earlier roots. (AC6)
_Last changed by 126-installed-harnesses._

### Uninstall
`brainrc uninstall` SHALL remove every link whose target is a path brainrc links to under any source root recorded in the manifest or configured now, the hook groups and MCP servers brainrc owns, and the files and directories that leaves empty (never a harness home), SHALL back up every file it rewrites, SHALL restore an instructions file `init` moved aside, SHALL keep local config and packs unless `--purge`, SHALL refuse `--purge` when the settings home is ~, holds ~ or a harness home, or holds a file brainrc didn't make, SHALL ignore manifest entries with a path outside ~, a `hooks_dir` that holds the harness home, or a root that is ~ or holds it, and SHALL change nothing with `--dry-run`. (AC1, AC2, AC3, AC4, AC5, AC6, AC7)
_Last changed by 128-brainrc-uninstall._

### Repair links after a move
`brainrc apply --repair` (and `status --repair`, which writes nothing) SHALL relink a link whose target is under a source root recorded in the manifest, or is missing and ends with the planned source's last two path parts, and SHALL prune links whose item is gone that point into a recorded root, or into a root inferred from a broken link that no longer exists and is not ~ or one of its ancestors; it SHALL ignore recorded roots that are ~, / or an ancestor of ~, and every other link it doesn't manage, the user's live links included, SHALL stay as it is. (AC1, AC2, AC3, AC4, AC5)
_Last changed by 129-apply-repair._

### Claude Code config dir from CLAUDE_CONFIG_DIR
`brainrc` SHALL resolve every claude path in harnesses.toml from `CLAUDE_CONFIG_DIR` when it holds an absolute path, and from `~/.claude` when it is unset, empty or relative, for `status`, `apply`, `doctor` and `uninstall` alike. (AC1, AC2, AC3, AC4)
_Last changed by 132-claude-config-dir._

### Codex home from CODEX_HOME
`brainrc` SHALL resolve every codex path in harnesses.toml from `CODEX_HOME` when it holds an absolute path, and from `~/.codex` when it is unset, empty or relative, for `status`, `apply`, `doctor` and `uninstall` alike. (AC1, AC2, AC3, AC4)
_Last changed by 133-codex-home._
