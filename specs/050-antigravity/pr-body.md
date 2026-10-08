## Summary
Antigravity CLI (`agy`), which replaced Gemini CLI, can now install ai-config as a plugin. Step 3 of #50; refs #50.

```text
agy plugin install https://github.com/bxker/ai-config
```

**Built from public sources, not run against a real `agy`.** Google's docs site and the `agy` installer were blocked in the build environment. The sources are the antigravity-cli CHANGELOG and issues, plus plugins that record tested behavior (MemPalace; CoalHearth on agy 1.3.1). The README and `docs/harness-packages.md` say so.

- **Root `plugin.json`** (`{"name": "ai-config"}`): `agy plugin install` needs it at the repo root. `aicfg plugin` generates it, and `validate` fails when it's missing or stale.
- **Rules get `trigger: always_on` frontmatter.** Antigravity silently drops plugin rules without a trigger. `aicfg` strips the frontmatter wherever it reads rules, so the rendered `instructions.md` is byte-identical to main's. `validate` requires a trigger on core rules (packs are unaffected).
- **No guard hooks for Antigravity yet.** Its `PreToolUse` has no known "no objection" reply: an empty `{}` is reported to deny every call, and `allow` is documented as auto-approve. Hooks wait for a live test; the README points to agy's own permission settings.
- **`aicfg` syncs to Antigravity in place of Gemini CLI:** skills go to `~/.gemini/config/skills` and rules to `~/.gemini/config/AGENTS.md`. The `gemini` harness stays in `harnesses.toml` but disabled, so the next `apply` removes its old links. It can be re-enabled in `harnesses.local.toml` for accounts still on Gemini CLI.
- **Docs say Antigravity wherever they said Gemini:** README, `docs/{formats,architecture,guardrails,spec-agent,troubleshooting,harness-packages}.md`, spec-agent's fallback, `overrides/README.md`, `mcp/servers.toml`, and AGENTS.md. Only the CHANGELOG history and one retirement line still name Gemini CLI. The roadmap's Gemini TOML adapter is dropped. `VERSION` 0.3.18.

## Acceptance criteria
- [x] AC1 root `plugin.json` generated and checked
- [x] AC2 rule `trigger` frontmatter, stripped by aicfg, required on core rules
- [x] AC3 no Antigravity guard hooks; README says so
- [x] AC4 docs, VERSION, CHANGELOG
- [x] AC5 tests, validates, real `apply`

## Testing
- `python3 -m unittest discover -s tests -q` → OK (132). The new tests failed first.
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.
- `apply` in a fake home directory: the rendered `instructions.md` is identical to main's.
- Upgrade in a fake home directory, from main's config to this branch: the 26 `~/.gemini/skills` links and `GEMINI.md` are removed, 26 skills and `AGENTS.md` are linked under `~/.gemini/config/`, and `doctor` is clean.
- Codex 0.161.0 reinstall in a scratch folder: installs 0.3.18 with the new root `plugin.json` present.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
