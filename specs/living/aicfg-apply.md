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
