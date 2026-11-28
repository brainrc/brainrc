## Summary
OpenCode now runs ai-config's guards (#50; refs #50). `apply` links `overrides/opencode/plugin.js` to `~/.config/opencode/plugins/ai-config-guard.js` through a new harness key, `plugin`.

- **What the plugin does:** it maps OpenCode's `bash`, `read`, `write`, `edit` and `grep` calls to the payload the guards read, then runs the same `guard_outward.py` and `guard_secrets.py` as Claude Code's hooks. It finds them through its own real path, so it works from a checkout and from an installed package.
- **Deny only.** An OpenCode plugin can't prompt, so anything the guards would ask about is **blocked**. The model gets the guard's reason plus "ask the user to run it themselves".
- **Fails open:** if Python or a guard can't run, the call is allowed, matching a broken Claude Code hook.
- **Not guarded yet:** MCP tools, because OpenCode's `server_tool` names can't be split reliably.
- **`aicfg` changes:** the `plugin` link is created, pruned and checked by `doctor`, and `validate` requires the file for any harness that sets the key.
- `VERSION` 0.3.25.

## Acceptance criteria
- [x] AC1 plugin maps tools, blocks with the reason, fails open
- [x] AC2 `plugin` harness key: link, prune, doctor, validate
- [x] AC3 tests and a real OpenCode load
- [x] AC4 docs, VERSION, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK (169).
- **The plugin under Node 22:** it blocks `git push`, reading `.env` and writing a private key, and lets `git status`, reading `README.md` and an MCP-style tool through. These tests are skipped where Node isn't installed.
- **Real OpenCode 1.18.35**, after `apply` in a fake home directory: `opencode debug config` lists the linked plugin. Inside OpenCode's own runtime (Bun 1.3.14), a throwaway probe plugin loaded ours through the link, and it blocked `git push` with the guard's reason.
- **Not verified:** the hook firing on a model's tool call, because that needs a model login. Commands you type yourself with `!` don't go through plugin hooks, by design.
- The checkout transcript matches 0.3.24 except for the new plugin link.
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
