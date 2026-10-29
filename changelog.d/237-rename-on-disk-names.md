---
bump: patch
---
- `apply` now writes brainrc names for the Codex MCP block markers, the OpenCode guard link (`brainrc-guard.js`) and the git pack fetch record (`.git/brainrc-fetched.json`). It still recognizes the old ai-config ones: it replaces an old Codex block in place, prunes the old guard link when it points at the managed guard, and reads then removes the old fetch record, so nothing is duplicated or re-fetched.
