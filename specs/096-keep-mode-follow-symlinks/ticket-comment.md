`aicfg apply` now keeps a settings or MCP file's permissions, so a `0600` `~/.claude.json` stays `0600`. It also writes a symlinked file through to its target and leaves the link in place. Backups keep the mode and sit next to the target.
Verify: `python3 -m unittest -v tests.test_mcp.McpSyncTest tests.test_aicfg.SyncFakeHomeTest`.
PR: <PR_URL>
