Keep file mode and follow symlinks when aicfg writes config

1 of 4 in epic #92 (E1: Safe writes and fail-open hooks).

## Why
`aicfg apply` wrote settings and MCP files through a temp file created with the umask mode, then renamed it over the path. A `0600` `~/.claude.json`, which can hold MCP tokens, came back `0644`. A symlinked `settings.json` was replaced by a plain file, so the merged hooks never reached the dotfiles target.

## What changed
- New `replace_file` in `aicfg/settings.py`, used by `write_settings` and `write_mcp`. It resolves the path, then backs up, writes the temp file, and renames, all next to the target, so the link survives.
- The temp file and the backup are created `0600` (with `O_EXCL`, after removing a stale temp file) and given the target's mode just before the rename. Files that don't exist yet still get the umask default.
- `docs/troubleshooting.md` covers permissions, symlinks, and MCP backups. New living area `specs/living/aicfg-apply.md`.

## Acceptance criteria
- [x] AC1: 0600 MCP file stays 0600, verified by `test_mcp.McpSyncTest.test_a_private_claude_json_stays_private` and a manual apply
- [x] AC2: settings file mode kept, verified by `test_settings_write_keeps_the_files_mode`
- [x] AC3: symlinked settings stays linked and the target gets the hooks, verified by `test_symlinked_settings_stay_linked_and_the_target_gets_the_hooks`
- [x] AC4: symlinked MCP file stays linked and keeps its target's mode, verified by `test_a_symlinked_claude_json_stays_linked`
- [x] AC5: temp file is never looser than 0600 for a 0600 target, even with umask 0, verified by `test_temp_file_is_never_looser_than_the_target`
- [x] AC6: backup sits next to the target with the old content and no temp file is left, verified by the AC3 test
- [x] AC7: a dangling link creates its target, verified by `test_a_dangling_settings_link_creates_its_target`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- Files are now written as UTF-8 bytes, so Windows no longer gets `\r\n` line endings or the locale encoding. The JSON is ASCII, and UTF-8 is correct for TOML.
- Backups no longer keep the original's mtime. They sort by name, so nothing reads it.
- A symlink loop makes `resolve()` raise. `apply` fails and leaves the file alone.
- `os.chmod` acts on the path rather than `fchmod` on the fd. Swapping the file in between needs write access to the user's config dir.
- A newly created MCP file still gets the umask default. Creating it `0600` could be its own ticket.

Spec: `specs/096-keep-mode-follow-symlinks/spec.md` · Plan: `specs/096-keep-mode-follow-symlinks/plan.md`
Closes #96
