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
