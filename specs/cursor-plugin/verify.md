# Verify: cursor-plugin

| Criterion | Evidence | Result |
|---|---|---|
| AC1 manifest | `aicfg plugin` writes `.cursor-plugin/plugin.json` and `hooks.json`; `CursorPluginTest` (manifest fields, missing file reported, rules need `alwaysApply`). The manifest validates against cursor/plugins `schemas/plugin.schema.json` (ccb5507) with ajv 8; a bad manifest fails it (negative control). | pass |
| AC2 adapter | `CursorGuardTest` (7): denies `git push`, `cat .env`, reading `.env`; allows `ls`, `README.md`, bad JSON, unknown events; works through a symlinked dir. Both generated commands run through `sh -c` with `HOME` / `CURSOR_PLUGIN_ROOT` set and deny reading `.env`. | pass |
| AC3 aicfg | `CursorHooksTest` (4): foreign entries kept, ours replaced, idempotent, `version: 1` added only when missing, Claude adds no keys, apply + doctor clean. Baseline transcript vs main: only the new Cursor link and merge lines; Claude settings identical. Installed wheel: `aicfg apply` links `~/.cursor/hooks/ai-config` into the package and the guard denies `git push`. | pass |
| AC4 tests | `python3 -m unittest discover -s tests` → 183 OK. `validate` core and pack OK. `claude plugin validate .` passes (existing CLAUDE.md warning). Tutorial runs clean. | pass |
| AC5 docs | README, formats, guardrails, harness-packages, roadmap, AGENTS.md, CHANGELOG 0.3.26, VERSION. | pass |

Not verified: a real Cursor (cursor.com and its downloads are blocked here): whether it loads
`.md` rules, accepts our agents' `model` values, expands `$HOME` in hook commands, and fires the hooks.
