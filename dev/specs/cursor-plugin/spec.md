# Spec: Cursor installs ai-config as a plugin and runs its guards

Ticket: gh:50 (refs) · Size: standard (generated manifest, hook adapter, settings merge, tests) · Status: draft

## Background
cursor.com is blocked here, so the format comes from Cursor's official plugin repo
(github.com/cursor/plugins at ccb5507, 2026-10-07: `schemas/plugin.schema.json`, its plugins, and
its scaffold skill), plus hook payload types from the community `cursor-hooks` npm package.
- Manifest: `.cursor-plugin/plugin.json`, only `name` required, unknown keys rejected. `skills`,
  `agents`, `rules`, `commands` take paths; `hooks` takes a path or an inline object. Paths are
  relative, inside the plugin, no `..`. Without paths, Cursor discovers default directories.
- Local install: a plugin directory (or a symlink to one) at `~/.cursor/plugins/local/<name>/`.
- Rules need frontmatter: `alwaysApply: true` for always-on.
- Hooks: `{"version": 1, "hooks": {"<event>": [{"command": "..."}]}}`, user file
  `~/.cursor/hooks.json`, `${CURSOR_PLUGIN_ROOT}` in plugin hooks. `beforeShellExecution` gets
  `{command}`, `beforeReadFile` `{file_path, content}`. Reply `{"permission": "allow"|"deny"|"ask",
  "user_message", "agent_message"}`; `beforeReadFile` takes only allow or deny; `ask` was reported
  broken (2.4.21). Exit 2 blocks; other failures allow.
- A search result says Cursor falls back to `.claude-plugin/plugin.json` when `.cursor-plugin/` is
  missing. That would load Claude's hook format, which Cursor rejects, so we ship our own manifest.

## Acceptance criteria
- **AC1** `aicfg plugin` also writes `.cursor-plugin/plugin.json`: name, version, description,
  author, license, `skills: "./skills/"`, `agents: "./agents/"`, `rules: "./rules/"`, and inline
  `hooks` running the adapter through `${CURSOR_PLUGIN_ROOT}`. `validate` reports it missing or
  stale like the other manifests. Every `rules/*.md` gains `alwaysApply: true` (validate requires
  it; aicfg still strips frontmatter).
- **AC2** `overrides/cursor/hooks/guard.py` (stdlib) turns `beforeShellExecution` into a Claude
  Bash payload for `guard_outward.py` and `guard_secrets.py`, and `beforeReadFile` into a Read
  payload for `guard_secrets.py`. It finds the guards through its own real path, so it works from
  the plugin, an aicfg link, and an installed copy. Ask or deny → `deny`, with the guard's reason
  and "ask the user to run it themselves" (open choice below). A guard that fails to run, or a
  payload it doesn't know, → allow, like Claude Code.
- **AC3** aicfg: `[cursor]` gains `hooks_dir = "~/.cursor/hooks/ai-config"` and
  `settings = "~/.cursor/hooks.json"` with `overrides/cursor/settings.fragment.json`. The merge
  recognizes Cursor's flat `{command}` entries as owned, keeps other tools' entries, and adds
  `version: 1` to a new file. Claude's merge is unchanged (baseline transcript identical apart from
  the new Cursor lines).
- **AC4** Tests: the adapter blocks `git push` and reading `.env` and lets `ls` and `README.md`
  through; bad JSON and unknown events allow; the manifest is generated and checked; the Cursor
  merge is idempotent and keeps foreign entries. The manifest validates against Cursor's schema
  (checked once here, not in CI).
- **AC5** Docs: README (Cursor install: symlink a checkout to `~/.cursor/plugins/local/ai-config`;
  one path, not both), `docs/formats.md`, `docs/guardrails.md`, `docs/harness-packages.md`
  (evidence and what's unverified), roadmap, CHANGELOG, VERSION 0.3.26.

## Open choice
- **Ask handling.** (A, recommended) Deny both, like OpenCode: safe if Cursor's `ask` is broken.
  (B) Pass `ask` through for shell commands, deny for reads: a real prompt where it works, but a
  silent allow where it's broken.

## Not in this step
A marketplace listing, MCP and file-write guarding (no reliable pre-write hook payload), a live
Cursor run (no Cursor binary here), and rules for aicfg-only Cursor users (no user rules file).
