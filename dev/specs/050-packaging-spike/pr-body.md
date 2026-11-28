## Summary
Records the #50 packaging spike in `docs/harness-packages.md`. Refs #50, which stays open for the build tickets.

- **What it covers:** for each harness (Claude Code, Codex, Gemini CLI, OpenCode, Cursor), the package format and install command, how rules load without a clone, hooks (and whether they can ask), agents, and how packs would be found.
- **Sources:** each section links its sources and marks what's unconfirmed. The Codex, OpenCode and Cursor docs sites were blocked during research, so those sections say where their findings came from instead: the Codex and OpenCode source repos, and search excerpts and forum posts for Cursor.
- **Key findings:**
  - Codex reads `.claude-plugin/` directly.
  - Codex skips commands that use `$ARGUMENTS`.
  - Only Claude Code's hooks reliably support ask.
  - Rules and pack extensions need rendering outside the checkout first.
- **Proposed order for #50:** `$AICFG_HOME` rendering → Codex via `.claude-plugin/` → Gemini extension → OpenCode → Cursor → packs as packages.
- The roadmap points to #50 and drops the items that have shipped (parallel tasks, plugin packaging).
- `VERSION` 0.3.15, with the plugin manifests regenerated.

## Testing
- `python3 scripts/aicfg.py validate` and `validate --pack examples/pack-acme` → OK
- `python3 -m unittest discover -s tests -q` → OK

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
