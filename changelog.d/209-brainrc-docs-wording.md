---
bump: patch
---
- **[pack contract]** Everything now says brainrc. The old names (the `aicfg` command, `scripts/aicfg.py`, `python -m aicfg`, `import aicfg`, `AICFG_HOME`, `~/.config/ai-config`, `hooks/ai-config*`, `ai-config@ai-config`) keep working with a warning until 0.5.0, which removes them. Run `brainrc migrate` and reinstall the plugin before then.
