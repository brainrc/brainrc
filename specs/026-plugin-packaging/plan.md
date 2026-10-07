# Plan: Claude Code plugin and marketplace

Inline mode, tests first. One review pass over the whole diff before Verify.

| Task | What | Files | Criteria | Red test |
|---|---|---|---|---|
| T1 | `plugin_manifests() -> dict[path, text]`, `cmd_plugin()` writes them, `check_plugin()` used by `validate` | `scripts/aicfg.py`, `tests/test_aicfg.py` | AC1, AC2, AC6 | `PluginTest`: generated plugin.json has `VERSION`, hooks use `${CLAUDE_PLUGIN_ROOT}/overrides/claude/hooks` and no `{{hooks_dir}}`; second run writes nothing; `validate` fails naming the file when missing or when `VERSION` changes |
| T2 | Generate the manifests; real `claude plugin validate .`; spec-agent `ai-config:<role>` fallback | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `skills/spec-agent/SKILL.md` | AC3, AC5 | `claude plugin validate .` output recorded |
| T3 | Docs and release; regenerate the manifests after the `VERSION` bump | `README.md`, `docs/packs.md`, `docs/troubleshooting.md`, `VERSION`, `CHANGELOG.md`, `.claude-plugin/*` | AC4, AC6 | `validate` (stale check) |

## Cross-task note
T1's stale check makes `validate` fail on main's state until T2 commits the manifests: T1 and
T2 land in one push, and the repo's `ValidateTest` stays red between them.

## Risks
- The test that the repo validates clean (`ValidateTest`) depends on the committed manifests;
  every future `VERSION` bump must run `aicfg plugin`. CONTRIBUTING and the CHANGELOG policy
  get one line saying so.
