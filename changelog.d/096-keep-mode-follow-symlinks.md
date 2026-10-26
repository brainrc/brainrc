---
bump: patch
---
- `aicfg apply` keeps a settings or MCP file's permissions when it rewrites it, so a `0600` `~/.claude.json` no longer comes back world-readable, and writes through a symlinked file to its target instead of replacing the link. Backups keep the original's permissions and sit next to the target.
