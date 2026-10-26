---
bump: patch
---
- `aicfg apply` takes a lock on `$AICFG_HOME/apply.lock`, so a second apply exits with a clear message instead of overwriting the first one's writes. Temp files carry the pid. A settings or MCP file that changes while apply runs (Claude Code rewriting `~/.claude.json`) is left alone with a `CHANGED` warning and exit 1, instead of losing that write.
