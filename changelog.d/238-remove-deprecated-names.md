---
bump: minor
---
- **[pack contract]** 0.5.0 removes the old names that have warned since 0.4.0. Use `brainrc` for the `aicfg` command, `scripts/brainrc.py` for `scripts/aicfg.py`, and `python -m brainrc` / `import brainrc` for `python -m aicfg` / `import aicfg` (the `aicfg_home` alias is gone too). Use `BRAINRC_HOME` for `AICFG_HOME`. The legacy `~/.config/ai-config` and `AICFG_HOME` are no longer read: while either holds an unmigrated home, `status`, `apply` and `update` write nothing and exit 1 naming `brainrc migrate`, and `doctor` reports a FAIL. Run `brainrc migrate` to move it. Packs should allow `requires_core` `<0.6`.
