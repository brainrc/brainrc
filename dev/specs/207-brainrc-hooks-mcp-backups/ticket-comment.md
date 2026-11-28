Draft PR: https://github.com/brainrc/brainrc/pull/233

Hook links are now `hooks/brainrc(-<pack>)`. One `apply` on an old install replaces the old-name settings and hooks.json entries (each hook once), removes the old links, and honors MCP ownership records left in `~/.config/ai-config`. Backups are `.bak-brainrc-*`, and old `.bak-aicfg-*` count toward the 5 kept.
