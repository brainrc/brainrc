# Verify: Keep file mode and follow symlinks on every write

Run at 2026-10-25T19:39:15Z on commit `09d235f`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 373 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_mcp.McpSyncTest.test_a_private_claude_json_stays_private` passes; manual: fresh HOME, 0600 `~/.claude.json`, `aicfg apply` with one server → `MERGE claude ~/.claude.json (mcp)`, file `-rw-------`, `userID` kept, `mcpServers: ['docs']` | pass |
| AC2 | `test_aicfg.SyncFakeHomeTest.test_settings_write_keeps_the_files_mode` passes (0600 and 0640) | pass |
| AC3 | `test_aicfg.SyncFakeHomeTest.test_symlinked_settings_stay_linked_and_the_target_gets_the_hooks` passes; manual: symlinked `~/.claude/settings.json` → still a link to `dotfiles/settings.json`, target has `theme` and `hooks` | pass |
| AC4 | `test_mcp.McpSyncTest.test_a_symlinked_claude_json_stays_linked` passes (link kept, target merged, target 0600) | pass |
| AC5 | `test_aicfg.SyncFakeHomeTest.test_temp_file_is_never_looser_than_the_target` passes (umask 0, temp is 0600 at rename) | pass |
| AC6 | `test_symlinked_settings_stay_linked_and_the_target_gets_the_hooks` asserts one backup beside the target with the old content, none beside the link, no `*.aicfg-tmp`; manual: `dotfiles/settings.json.bak-aicfg-20261025T193854Z` created, no temp left | pass |
| AC7 | `test_aicfg.SyncFakeHomeTest.test_a_dangling_settings_link_creates_its_target` passes | pass |

## Notes
- Mode tests skip on Windows (`os.name == "nt"`); not run there.
- Backups now keep the target's mode (manual: `.claude.json.bak-aicfg-*` is `-rw-------`).
- Manual run used a `git archive` copy of HEAD and a fresh scratch HOME; nothing in the real HOME was touched.
