`aicfg apply` now holds `$AICFG_HOME/apply.lock`, so a second apply exits 1 with a clear message instead of writing. Temp names include the pid. A settings or MCP file that changes mid-apply (Claude Code rewriting `~/.claude.json`) is left alone with a `CHANGED` warning. `docs/troubleshooting.md` covers both messages and says to close Claude Code first.
Verify: `python3 -m unittest -v tests.test_aicfg.SyncFakeHomeTest tests.test_mcp.McpSyncTest`.
PR: <PR_URL>
