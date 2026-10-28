---
bump: patch
---
- **[pack contract]** The plugin and marketplace are now `brainrc@brainrc`, and skills and agents
  show as `brainrc:<name>` (`/brainrc:work`) in Claude Code, Codex, Cursor and Antigravity. Plugin
  users uninstall `ai-config@ai-config` and its marketplace, then install `brainrc@brainrc`
  ([moving from ai-config](docs/install.md#moving-from-ai-config)); `brainrc doctor` warns while
  the old plugin is still installed in Claude Code or Cursor. Packs whose plugin `dependencies`
  name `ai-config` must name `brainrc`.
