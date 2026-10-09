# Spec: OpenCode runs ai-config's guards

Ticket: gh:50 (refs) · Size: standard (JS plugin, aicfg link kind, tests across Python/Node) · Status: approved

## Background
OpenCode plugins are JS modules loaded from `~/.config/opencode/plugins/`. `tool.execute.before`
gets `{tool}` and `output.args` and can block a call by throwing; the error goes back to the model.
A plugin can't make OpenCode prompt. Tool args (OpenCode source): `bash` `{command}`; `read`
`{filePath}`; `write` `{filePath, content}`; `edit` `{filePath, newString}`; `grep` `{path, include}`.

## Acceptance criteria
- **AC1** `overrides/opencode/plugin.js` maps OpenCode's `bash`, `read`, `write`, `edit`, `grep`
  calls to the Claude payload the guards read, and runs `guard_outward.py` and `guard_secrets.py`
  (found through the plugin file's real path, so it works from a checkout and an installed copy).
  An `ask` or `deny` decision blocks the call, and the error carries the guard's reason plus
  "ask the user to run it themselves". If Python or a guard fails to run, the call is allowed,
  matching Claude Code's hook behavior. MCP tools aren't guarded: OpenCode's `server_tool` names
  can't be split reliably.
- **AC2** New harness key `plugin` (a file path): `apply` links it to
  `overrides/<harness>/plugin.js`, prunes it when removed, and `doctor` checks it.
  `[opencode] plugin = "~/.config/opencode/plugins/ai-config-guard.js"`.
- **AC3** Tests: the plugin, run with Node when Node is installed (skipped otherwise), blocks
  `git push` and reading `.env`, and lets `ls` and reading `README.md` through. The link is
  created, pruned and checked. Real OpenCode 1.18.35 loads the plugin without error.
- **AC4** Docs: the `docs/formats.md` table (OpenCode guard hooks ✅, deny only),
  `docs/guardrails.md`, `docs/harness-packages.md`, README if it mentions guards; CHANGELOG;
  VERSION 0.3.25.

## Not in this step
MCP tool guarding, an "approve" escape hatch, and the guard running inside a no-clone OpenCode
package (an npm plugin).
