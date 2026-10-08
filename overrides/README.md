# overrides/

Harness-specific config that has no cross-tool equivalent, one folder per
harness (`claude/`, `codex/`, `opencode/`, `antigravity/`, `cursor/`). Examples:
Claude `settings.json` hooks, Codex `config.toml` model defaults.

`claude/` is synced: `hooks/` is symlinked to the harness's `hooks_dir`, and
`settings.fragment.json` is merged into its `settings` file, with `{{hooks_dir}}` replaced
by that path. Other harnesses aren't synced yet (see [roadmap](../docs/roadmap.md)).
Secret values never go here.
