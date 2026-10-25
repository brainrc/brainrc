---
bump: patch
---
- Guard hooks fail open when their script is missing, so a moved or deleted checkout (or a Python upgrade) no longer blocks every Claude Code tool call. Cursor's guard replies allow. Run `apply` to rewrite existing hook commands.
- `aicfg doctor` runs each ai-config hook with an empty payload and reports one that is missing, exits non-zero, times out, or has no `python3`.
