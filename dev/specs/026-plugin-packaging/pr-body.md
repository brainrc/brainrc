## Summary
ai-config can now be installed as a Claude Code plugin, without cloning or running `aicfg`. Closes #26.

```text
/plugin marketplace add bxker/ai-config
/plugin install ai-config@ai-config
```

- **The repo is both the marketplace and the plugin** (`"source": "."`). Its default `skills/`, `agents/` and `commands/` folders are the plugin's components.
- **`aicfg plugin` generates `.claude-plugin/plugin.json` and `marketplace.json` from the repo:**
  - the version comes from `VERSION`;
  - the hooks come from `overrides/claude/settings.fragment.json`, with `{{hooks_dir}}` replaced by `${CLAUDE_PLUGIN_ROOT}/overrides/claude/hooks`;
  - the author is "ai-config contributors", so no personal details.

  The files are committed so GitHub installs work. `validate`, which runs in CI, fails when they're stale. AGENTS.md and CONTRIBUTING say to run it after every `VERSION` bump.
- **What the plugin doesn't cover:** rules (plugins can't load instructions into every session), packs and other harnesses still need `aicfg`. The README has a table and says to pick one install path.
- **spec-agent:** in subagent mode it falls back to `ai-config:<role>` when the plain role name isn't found.
- **Packs decision:** packs stay `aicfg` packs, because their rules and spec-agent extensions need `aicfg` to render them. Recorded in `docs/packs.md`.
- **Troubleshooting:** a new symptom for every skill showing up twice, or a hook running twice.

## Acceptance criteria
- [x] AC1 generated from the repo; running it again changes nothing
- [x] AC2 `validate` fails when a manifest is stale or missing
- [x] AC3 `claude plugin validate .` passes
- [x] AC4 README, packs decision, troubleshooting
- [x] AC5 spec-agent role-name fallback
- [x] AC6 tests, VERSION 0.3.14, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK. 4 new tests, each seen failing on an assertion first.
- `claude plugin validate .` (CLI 2.1.292) → passes. The only warning is that the root `CLAUDE.md`, which is for contributors, isn't loaded by plugins.
- Real install into a fresh fake home directory: marketplace added, plugin installed and enabled. The `roles` symlink survives in the installed copy, and its guard hook asks on `git push` and allows `git status`.
- Real stale check: bumping `VERSION` made `validate` fail and name `aicfg plugin` as the fix.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
