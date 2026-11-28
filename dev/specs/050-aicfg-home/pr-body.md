## Summary
`apply` now renders the rules and spec-agent extensions to `$AICFG_HOME` (default `~/.config/ai-config/`) instead of into the checkout. Packaged installs, like a plugin cache or an extension folder, can then read them. Step 1 of #50; refs #50.

- **`aicfg_home()`:** `$AICFG_HOME` if set, otherwise `~/.config/ai-config`. `instructions.md` and `extensions.md` are written there.
- **Upgrading:** an existing link to `dist/instructions.md` shows as `UPDATE`, and the next `apply` re-points it. The old file and the emptied `dist/` folder are removed.
- **Pruning:** a disabled harness's link to the new location is pruned as before.
- **`doctor`:** it checks the files in `$AICFG_HOME` and shows their `~` paths.
- **Readers:** spec-agent and `ticket-jira` read `$AICFG_HOME/extensions.md` first and fall back to `references/extensions.md`.
- **Docs:** README, `harnesses.toml`, architecture, packs, troubleshooting and the tutorial are updated.

**[pack contract]**, non-breaking: the in-repo `skills/spec-agent/references/extensions.md` is still written, but it's deprecated, and a later MINOR release stops writing it. So this is a PATCH bump to 0.3.16.

## Acceptance criteria
- [x] AC1 renders to `$AICFG_HOME`, with the default under the home directory
- [x] AC2 links re-pointed when upgrading; pruning unchanged
- [x] AC3 old `dist/instructions.md` removed
- [x] AC4 spec-agent and `ticket-jira` read the new path first
- [x] AC5 `doctor` checks the new location
- [x] AC6 docs
- [x] AC7 tests, tutorial, VERSION, CHANGELOG, plugin manifests

## Testing
- `python3 -m unittest discover -s tests -q` → OK. 6 new tests, each seen failing first. The tests set `AICFG_HOME` to a temp directory, so they never touch the real `~/.config`.
- `specs/013-tutorial/run-tutorial.sh` → ran clean.
- Real `apply` in a fake home directory: both files written, the link points at them, `status` reports everything in sync, and `doctor` is clean.
- Real upgrade from a `dist/` link: `UPDATE`, link re-pointed, old file removed, `doctor` clean.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
