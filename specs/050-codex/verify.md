# Verify: Codex installs ai-config from the existing plugin

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `git mv` of the 5 commands to `skills/<name>/SKILL.md` (shown as renames); each adds `name`, `argument-hint`, `disable-model-invocation: true`, and the no-substitution line; core `commands/` gone; `validate`: 26 skills, 0 commands; pack fixture still ships a command (`validate --pack`: 1 command) | pass |
| AC2 | `SKILL.md` note under the Roles table; `references/fallback.md` step 2 | pass |
| AC3 | Real upgrade in a fake HOME: `apply` from `main` linked `~/.claude/commands/*.md` and `~/.codex/prompts/*.md`; `apply` from this branch emptied both and linked `~/.claude/skills/work` etc. for every harness; `doctor`: No problems found | pass |
| AC4 | `UserInvokedSkillTest` (red first: `commands/` existed) | pass |
| AC5 | Real Codex 0.161.0 reinstall (fresh CODEX_HOME): installed copy has `skills/{work,review,spec-status,spec-approve,spec-resume}` and `agents/`; no `commands/` | pass |
| AC6 | README (layout line, plugin section, Codex install), `docs/formats.md`, `docs/harness-packages.md` (Codex marked verified), `docs/spec-agent.md`, AGENTS.md; VERSION 0.3.17; CHANGELOG; `aicfg plugin`; `claude plugin validate .` passes (only the CLAUDE.md note) | pass |

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK; `validate --pack examples/pack-acme` → OK
- `bash specs/013-tutorial/run-tutorial.sh` → tutorial ran clean

## Not verified
Codex running the plugin's guard hooks, and loading rules: needs a logged-in Codex session.
