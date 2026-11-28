Shipped: the settings home is `BRAINRC_HOME`, else `$XDG_CONFIG_HOME/brainrc`, else `~/.config/brainrc`. An existing `~/.config/ai-config` or `AICFG_HOME` keeps working until 0.5.0 with one warning per run.
`brainrc migrate --dry-run`, then `brainrc migrate`, moves the old home and re-runs `apply`. `brainrc doctor` reports an old home that hasn't been migrated. This also closes #131 (XDG_CONFIG_HOME).
PR: https://github.com/brainrc/brainrc/pull/232
