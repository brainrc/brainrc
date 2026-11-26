# overrides/

Harness-specific config that has no cross-tool equivalent, one folder per
harness (`claude/`, `codex/`, `opencode/`, `antigravity/`, `cursor/`). Examples:
Claude `settings.json` hooks, Codex `config.toml` model defaults.

`apply` syncs what a harness's `harnesses.toml` entry has a key for:
- `claude/`, `cursor/`, `codex/` and `antigravity/`: `hooks/` is symlinked to the harness's
  `hooks_dir`, and `settings.fragment.json` is merged into its `settings` file, with
  `{{hooks_dir}}` replaced by that path. Write every fragment in Claude Code's shape, hooks under
  `"hooks"`; Antigravity's file (`settings_format = "antigravity"`) gets them under its own entry,
  `brainrc`. The other harnesses' `hooks/guard.py` run Claude's guards through
  `claude/hooks/guard_bridge.py` and reply in their harness's format.
- `opencode/`: `plugin.js` (the guard plugin) is symlinked to the harness's `plugin` path.
Secret values never go here.
