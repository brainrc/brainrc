# overrides/

Harness-specific config that has no cross-tool equivalent, one folder per
harness (`claude/`, `codex/`, `opencode/`, `antigravity/`, `cursor/`). Examples:
Claude `settings.json` hooks, Codex `config.toml` model defaults.

`apply` syncs what a harness's `harnesses.toml` entry has a key for:
- `claude/` and `cursor/`: `hooks/` is symlinked to the harness's `hooks_dir`, and
  `settings.fragment.json` is merged into its `settings` file, with `{{hooks_dir}}` replaced
  by that path.
- `opencode/`: `plugin.js` (the guard plugin) is symlinked to the harness's `plugin` path.

Codex and Antigravity have no overrides yet.
Secret values never go here.
