# Plan: OpenCode runs ai-config's guards

No new dependency (Node's built-ins in the plugin; OpenCode runs it). New harness key `plugin`.

## Approach
- `overrides/opencode/plugin.js` (ES module, built-ins only): a tool map to the Claude payload,
  `spawnSync("python3", [guard])` with the payload on stdin and a 5 s timeout, the guards found
  at `../claude/hooks/` from the plugin's real path, and a throw on `ask`/`deny`. It fails open
  on spawn errors.
- `aicfg.plan`: a harness `plugin` key adds one core link to `overrides/<harness>/plugin.js`;
  stale detection includes it; `_managed_target` accepts `overrides/<harness>/plugin.js`.
  `harnesses.toml` `[opencode] plugin = "~/.config/opencode/plugins/ai-config-guard.js"`.
- `validate`: an `overrides/<harness>/plugin.js` exists for each harness that sets `plugin`.

## Tasks
| id | title | agent | files | criteria |
|---|---|---|---|---|
| T1 | tests first: plugin via Node; link, prune, doctor | implementer | tests/test_hooks.py, tests/test_aicfg.py | AC1–AC3 |
| T2 | plugin.js | implementer | overrides/opencode/plugin.js | AC1 |
| T3 | aicfg `plugin` key and harnesses.toml | implementer | aicfg/{plan,validate}.py, harnesses.toml | AC2 |
| T4 | real OpenCode loads it | implementer | none | AC3 |
| T5 | docs and release | implementer | docs/*, README.md, CHANGELOG.md, VERSION | AC4 |
