# Plan: Codex installs ai-config from the existing plugin

Inline mode, tests first. One review pass before Verify.

| Task | What | Files | Criteria | Red test |
|---|---|---|---|---|
| T1 | Test: user-invoked skill shape; no core `commands/` | `tests/test_aicfg.py` | AC4 | fails today: `commands/` exists |
| T2 | Move the 5 commands to skills (`git mv`, then frontmatter and the no-substitution line); remove `commands/` | `commands/*` → `skills/{work,review,spec-status,spec-approve,spec-resume}/SKILL.md` | AC1 | T1 test green; `validate` |
| T3 | spec-agent roles fallback | `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/fallback.md` | AC2 | n/a (prose) |
| T4 | Real checks: `apply` upgrade in a fake HOME (old command links pruned, skills linked); Codex reinstall shows the 5 skills | — | AC3, AC5 | recorded in verify.md |
| T5 | Docs, VERSION 0.3.17, CHANGELOG, `aicfg plugin` | `README.md`, `docs/{harness-packages,formats,spec-agent}.md`, `VERSION`, `CHANGELOG.md`, `.claude-plugin/*` | AC6 | `validate` |

## Risks
- Existing tests that count commands (tokens, sync) may assume core commands exist; adjust them
  to use the pack fixture's command.
- Always-loaded tokens: five more skill descriptions replace five command descriptions; budget
  check in `validate` catches growth.
