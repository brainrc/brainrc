---
bump: minor
---
- **[pack contract]** The tool is now `brainrc`: the PyPI distribution, the console script, the
  Python package (`import brainrc`, `python -m brainrc`), and the checkout entry
  `scripts/brainrc.py`. `brainrc --version` prints `brainrc <VERSION>`. The old names
  (`aicfg`, `scripts/aicfg.py`, `python -m aicfg`, `import aicfg`) keep working until 0.5.0,
  each printing one deprecation line on stderr; point packs' pre-commit hooks at
  `scripts/brainrc.py` before then. Installed users: run `uv tool uninstall ai-config` (or
  `pipx uninstall ai-config`) before installing `brainrc`, because both ship an `aicfg` command
  and removing the old one afterwards deletes the new shim. `AICFG_HOME` and
  `~/.config/ai-config` are unchanged for now.
