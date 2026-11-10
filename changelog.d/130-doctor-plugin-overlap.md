---
bump: patch
---
- `doctor` warns when the brainrc plugin and brainrc's own links are both installed in Claude Code (`brainrc@<marketplace>` in `~/.claude/plugins/installed_plugins.json`, unless disabled in `enabledPlugins`) or in Cursor (`~/.cursor/plugins/local/brainrc`), since together they load every skill and hook twice. The warning names which to remove: the Claude Code plugin (the links also bring the rules and packs), or brainrc's Cursor links (the plugin is how Cursor gets the rules).
