# Spec: Doctor detects double installs

Ticket: gh:130 · Size: small · Status: approved

## Problem
The docs say to use the brainrc plugin or brainrc's links, not both, but nothing checks. With
both, every skill and hook loads twice, and `doctor` says nothing.

## Goals
- `doctor` warns when the brainrc plugin and brainrc's links are both installed in a harness, and names which to remove.

## Non-goals
- Codex and Antigravity plugins: where they install isn't verified yet (docs/harness-packages.md).
- Removing either install for the user.

## Acceptance criteria
- **AC1**: Given `brainrc@<any marketplace>` in `~/.claude/plugins/installed_plugins.json` and brainrc's links in Claude Code, when the user runs `doctor`, then it WARNs that skills and hooks load twice and its fix names the plugin to uninstall, with `[claude] enabled = false` as the alternative.
- **AC2**: Given `~/.cursor/plugins/local/brainrc` (a link or directory) and brainrc's links in Cursor, then `doctor` WARNs and its fix names `[cursor] enabled = false`, with removing the plugin as the alternative.
- **AC3**: No warning when only one of the two is installed, when the Claude plugin is disabled in `enabledPlugins`, or for another plugin; an unreadable plugin list is no warning. The WARN doesn't change doctor's exit code.

## Requirement changes
### Area: doctor
#### ADDED: Double install
`brainrc doctor` SHALL warn when the brainrc plugin (Claude Code's installed `brainrc@*`, unless disabled, or Cursor's `plugins/local/brainrc`) and brainrc's own links are both installed in that harness, naming which to remove. (AC1, AC2, AC3)

## Open questions
None. Defaults taken under `--oneshot`:
1. Claude Code: remove the plugin, since the links also bring rules and packs. Cursor: remove the links, since the plugin is how Cursor gets rules.
2. "brainrc's links" means at least one planned link in that harness is in place.
