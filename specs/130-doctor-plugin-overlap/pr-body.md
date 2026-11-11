Doctor warns when the brainrc plugin and its links are both installed

Part of epic #109 (E4), 6 of 6, stacked on #<PR_129>. Retarget to `main` before merging. Closes #130.

## Why
The docs say to use the brainrc plugin or brainrc's links, not both, since together they load every skill and hook twice. Nothing checked, and `doctor` said nothing.

## What changed
- `doctor` WARNs when Claude Code has `brainrc@<any marketplace>` in `~/.claude/plugins/installed_plugins.json` (and not disabled in `enabledPlugins`) and brainrc's links are in place. The fix says to uninstall the plugin, since the links also bring the rules and your packs, or else set `[claude] enabled = false`.
- The same for Cursor's `~/.cursor/plugins/local/brainrc`. There the fix says to drop brainrc's Cursor links with `[cursor] enabled = false`, since the plugin is how Cursor gets the rules, or else remove the plugin.
- The plugin list is read through the guards the old `ai-config` plugin check already used, now shared. A WARN doesn't change doctor's exit code.
- docs/troubleshooting.md says `doctor` checks this.

## Acceptance criteria
- [x] AC1: Claude Code plugin plus links warns and names the plugin to remove. Verified by `DoubleInstallTest` and `DoubleInstallDoctorTest`.
- [x] AC2: Cursor plugin plus links warns. Verified by `DoubleInstallTest`.
- [x] AC3: no warning with only one install, a disabled plugin or another plugin. Verified by `DoubleInstallTest`.

## How to verify
```
python3 -m unittest tests.test_doctor_plugin
python3 -m unittest discover -s tests
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Spec, Plan, Deliver. See `specs/130-doctor-plugin-overlap/log.md`.
- Which install to remove differs by harness: in Claude Code the links do more (rules, packs), and in Cursor the plugin does (rules).
- Codex and Antigravity plugins aren't checked, because where they install isn't verified yet.

## Follow-ups
- Check Codex and Antigravity plugins once their install locations are verified (E17).

Spec: `specs/130-doctor-plugin-overlap/spec.md` · Plan: `specs/130-doctor-plugin-overlap/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
