---
id: 237
title: Rename the on-disk names kept for compatibility
status: in-progress
pr:
---
Follow-up from #209: the Codex MCP block markers (`# >>> ai-config mcp servers`), the OpenCode
guard plugin link (`~/.config/opencode/plugins/ai-config-guard.js`) and the git-pack fetch record
(`.git/aicfg-fetched.json`) still use the old name. Rename each to brainrc, recognizing the old
name so an existing install converges on the next apply, and shrink the test_old_names allowlist.
