Add `brainrc uninstall`: take out what apply put into the harnesses

Part of epic #109 (E4), 4 of 6, stacked on #<PR_127>. Retarget to `main` before merging. Closes #128.

## Why
Removing brainrc meant disabling every harness and pack by hand, running `apply`, then deleting the repo. Once the checkout was gone, that no longer worked: links pointed nowhere, and brainrc's hooks and MCP servers stayed in your settings files.

## What changed
- New `brainrc uninstall` removes every link brainrc made, broken ones included. It also takes its hook groups out of each settings file, takes out the MCP servers it added, then removes the files and directories that leaves empty. A harness's own directory (`~/.claude`) always stays.
- Your own settings, hooks, servers and links stay. Every file it rewrites is backed up first, and a file left with nothing of yours in it is renamed to a backup, not deleted.
- It reads which harnesses and source roots `apply` used from `$BRAINRC_HOME/harnesses.json` (#126), so it works after the checkout or a pack is moved or deleted, or harnesses.local.toml is broken.
- An instructions file that `brainrc init` (#127) moved aside is put back.
- Rendered files in `$BRAINRC_HOME` go. Your local config and fetched packs stay unless you pass `--purge`, which deletes `$BRAINRC_HOME`. `--dry-run` prints every step and changes nothing.
- docs/troubleshooting.md's Uninstall section now uses the command.

## Acceptance criteria
- [x] AC1: configs match the pre-apply state plus your later edits. Verified by `UninstallTest`.
- [x] AC2: works after the checkout is deleted, or with a broken harnesses file. Verified by `UninstallTest`.
- [x] AC3: emptied files become backups, rewritten ones are backed up, unparsable ones are reported. Verified by `UninstallTest`.
- [x] AC4: empty dirs removed, never a harness home; local config stays. Verified by `UninstallTest`.
- [x] AC5: `--purge` and `--dry-run`. Verified by `UninstallTest`.
- [x] AC6: init's moved file is put back. Verified by `UninstallTest`.
- [x] AC7: nothing to do the second time; `apply` reinstalls. Verified by `UninstallTest`.

## How to verify
```
python3 -m unittest tests.test_uninstall
python3 -m unittest discover -s tests
python3 scripts/brainrc.py uninstall --dry-run
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Spec, Plan, Deliver. See `specs/128-brainrc-uninstall/log.md`.
- No confirmation prompt. It removes only what brainrc made, `--dry-run` shows the steps first, and every rewritten or emptied file is kept as a backup.
- The `*.bak-brainrc-*` backups stay after uninstall, since they're the only copy of earlier states.
- Without `--purge`, the generated files in `$BRAINRC_HOME` (rendered instructions and agents, the hooks copy, the manifest) are removed and your local files stay.

## Follow-ups
- None.

Spec: `specs/128-brainrc-uninstall/spec.md` · Plan: `specs/128-brainrc-uninstall/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
