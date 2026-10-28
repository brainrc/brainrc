---
bump: patch
---
- **[pack contract]** Everything now says brainrc. These old names keep working with a warning until 0.5.0 removes them: the `aicfg` command, `scripts/aicfg.py`, `python -m aicfg`, `import aicfg`, `AICFG_HOME` and the legacy `~/.config/ai-config` home. Run `brainrc migrate` to move the home.
- The next `apply` converges these silently: old `hooks/ai-config*` dirs and their settings entries, and `.bak-aicfg-*` backups.
- `brainrc doctor` flags the old `ai-config@ai-config` plugin until you uninstall it.
- Docs, README, AGENTS.md, CONTRIBUTING.md, skills, the example pack, messages and the pre-commit hook id now say brainrc.
- Some on-disk names are kept for compatibility and will change in a later follow-up: the Codex MCP block markers, the OpenCode `ai-config-guard.js` link and `.git/aicfg-fetched.json`.
