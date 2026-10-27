# aicfg-apply

How `aicfg apply` writes harness settings and MCP config files.

### Safe atomic writes
`aicfg apply` SHALL write settings and MCP files atomically, keep an existing file's permission
bits, and never expose the new content with looser permissions than the file had. (AC1, AC2, AC5)
_Last changed by 096-keep-mode-follow-symlinks._

### Symlinked config files
When a settings or MCP file path is a symlink, `aicfg apply` SHALL write through to the link's
final target (creating it if the link dangles), keep the link, and back up the target's previous
content. (AC3, AC4, AC6, AC7)
_Last changed by 096-keep-mode-follow-symlinks._

### One apply at a time
`aicfg apply` SHALL hold an exclusive lock while it writes, and a second apply SHALL exit
non-zero with a clear message instead of writing. Read-only commands SHALL NOT take the lock.
(AC1, AC2, AC5)
_Last changed by 097-apply-lock-unique-tmp._

### No lost concurrent writes
`aicfg apply` SHALL use per-process temp names, and SHALL NOT overwrite a settings or MCP file
whose content changed after apply read it; it warns and exits non-zero instead. (AC3, AC4)
_Last changed by 097-apply-lock-unique-tmp._

### Hooks fail open
ai-config's hook commands SHALL exit 0 without blocking (Cursor: with an allow response) when
their script file is missing, and behave as the guard otherwise. (AC1, AC2, AC3, AC7)
_Last changed by 098-hooks-fail-open._

### Doctor checks hooks
`aicfg doctor` SHALL report each ai-config hook in a harness's settings file whose script is
missing, or that exits non-zero for an empty payload, with the fix. (AC4, AC5, AC6)
_Last changed by 098-hooks-fail-open._

### Installed hooks live in AICFG_HOME
When `aicfg` runs from an installed package, `aicfg apply` SHALL copy core's hooks to
`$AICFG_HOME/hooks/core/<harness>/hooks/` and link `hooks_dir` there, refresh the copy when the
package's hooks change, and remove it when no harness with hooks is enabled. From a checkout, hooks SHALL
stay linked into the checkout. (AC1, AC2, AC3, AC4, AC5, AC6)
_Last changed by 099-hooks-in-aicfg-home._
