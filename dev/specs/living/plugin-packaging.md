# plugin-packaging

How brainrc is published as a plugin for each harness, and how an old install is flagged.

### Plugin and marketplace are named brainrc
`python3 scripts/brainrc.py plugin` SHALL write the Claude Code/Codex plugin and marketplace, Cursor
plugin and Antigravity `plugin.json` with name `brainrc` and author `brainrc contributors`, so installs
are `brainrc@brainrc` and skills appear as `brainrc:<name>`; `validate` SHALL fail on a stale manifest.
(AC1 to AC3)
_Last changed by 208-brainrc-plugin-namespace._

### Docs and roles use the new plugin names
Install docs SHALL give the `brainrc` commands and a move-from-`ai-config` note, and spec-agent SHALL
look roles up as `brainrc:<role>`, falling back to `ai-config:<role>`. (AC4 to AC6)
_Last changed by 208-brainrc-plugin-namespace._

### Doctor warns about the old plugin
`brainrc doctor` SHALL warn, read-only and with the fix, when the old `ai-config` plugin is installed
in Claude Code (key `ai-config@ai-config` in `~/.claude/plugins/installed_plugins.json`) or Cursor
(`~/.cursor/plugins/local/ai-config`), alone or next to `brainrc`, and SHALL stay silent, without
error, when that file is missing, unreadable or of an unexpected shape. (AC7 to AC11)
_Last changed by 208-brainrc-plugin-namespace._
