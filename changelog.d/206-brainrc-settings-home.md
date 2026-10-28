---
bump: patch
---
- **[pack contract]** The settings home is now `~/.config/brainrc` (`$XDG_CONFIG_HOME/brainrc`
  when that is set), overridden by `BRAINRC_HOME`. Rendered `instructions.md` and
  `extensions.md`, git packs, `*.local.toml`, and `rules/*.local.md` live there. An existing
  `~/.config/ai-config`, or `AICFG_HOME`, keeps working until 0.5.0 with one warning per run.
  `brainrc migrate` (try `--dry-run` first) moves the old directory and re-runs `apply`.
  `brainrc doctor` reports an old home that hasn't been migrated, and spec-agent's run pointer
  follows the same lookup. Reading `XDG_CONFIG_HOME` closes #131.
