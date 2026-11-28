## Summary
Cursor can install ai-config as a plugin and run its guards (#50 step 5; refs #50).

- **Plugin:** `aicfg plugin` also writes `.cursor-plugin/plugin.json` (skills, agents, rules) and `.cursor-plugin/hooks.json`. Install by symlinking a checkout to `~/.cursor/plugins/local/ai-config`. Every core rule gains `alwaysApply: true` so Cursor loads it, and `validate` requires it.
- **Guards:** `overrides/cursor/hooks/guard.py` sends `beforeShellExecution` (both guards) and `beforeReadFile` (secrets) through the same Python guards as Claude Code. Cursor's `ask` was reported broken and reads accept only allow or deny, so an ask **denies**, with the reason and "ask the user to run it themselves". If it can't run a guard, it allows the call.
- **aicfg:** `[cursor]` gains `hooks_dir` and `settings = "~/.cursor/hooks.json"`. The merge now recognizes Cursor's flat `{command}` entries as ours and adds `version: 1` to a new file. Claude's merge is unchanged.
- **Not covered:** file writes and MCP calls aren't guarded in Cursor (no reliable pre-write hook), and there's no marketplace listing.
- **Where the format comes from:** cursor.com is blocked here, so it comes from Cursor's official repo, [cursor/plugins](https://github.com/cursor/plugins) (schema, example plugins, scaffold skill), plus a community hook-types package. Details and open questions are in `docs/harness-packages.md#cursor`.
- `VERSION` 0.3.26.

## Acceptance criteria
- [x] AC1 generated `.cursor-plugin/` manifest; rules carry `alwaysApply: true`
- [x] AC2 guard adapter: deny on ask or deny; allows the call if a guard can't run
- [x] AC3 `[cursor]` hooks merge into `~/.cursor/hooks.json`
- [x] AC4 tests; manifest checked against Cursor's schema
- [x] AC5 docs, CHANGELOG, VERSION

## Testing
- `python3 -m unittest discover -s tests` → OK (183, 14 new).
- **The manifest** validates against `schemas/plugin.schema.json` from cursor/plugins with ajv; a deliberately bad manifest fails it.
- **Both generated hook commands**, run through `sh -c` as Cursor would, deny reading `.env`. From an installed wheel, `aicfg apply` links the hook dir into the package and the guard denies `git push`.
- The checkout transcript matches main except for the new Cursor link and merge lines; Claude's settings are byte-identical.
- `validate` (core and pack), `claude plugin validate .` and the tutorial script → OK.
- **Not verified in a real Cursor:** whether it loads `.md` rules, accepts our agents' `model` values, expands `$HOME` in hook commands, and fires the hooks.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
