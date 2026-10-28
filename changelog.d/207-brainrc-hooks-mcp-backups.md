---
bump: patch
---
- **[pack contract]** Hook links are now `hooks/brainrc` and `hooks/brainrc-<pack>` (was `hooks/ai-config*`). The next apply replaces old-name settings and hooks.json entries, removes the old links, and honors MCP ownership records left in a former home. Backups are `.bak-brainrc-*`; old `.bak-aicfg-*` count toward the 5 kept. Packs using `{{hooks_dir}}` need no change; hard-coded `hooks/ai-config` paths do.
