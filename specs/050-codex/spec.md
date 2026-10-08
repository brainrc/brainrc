# Spec: Codex installs ai-config from the existing plugin

Ticket: gh:50 (step 2 of 6; refs) · Size: standard (5 commands become skills, spec-agent fallback, docs) · Status: approved

## What a real Codex 0.161.0 install showed (scratch CODEX_HOME, fake HOME)
- `codex plugin marketplace add <repo>` reads our `.claude-plugin/marketplace.json`, and
  `codex plugin add ai-config@ai-config` installs version 0.3.16, enabled. No Codex-specific files needed.
- **The copy drops symlinks**: `skills/spec-agent/roles` is missing, so spec-agent's role links break.
- **None of the 5 commands arrive**: Codex skips commands that use `$ARGUMENTS`.
- Hooks (inline in `plugin.json`): no evidence Codex runs them; proving it needs a logged-in
  Codex session. Out of scope here.

Claude Code docs (skills): a skill is invoked as `/<name>` (plugin: `/<plugin>:<name>`), `$ARGUMENTS`
works in its body, and a skill beats a command of the same name. So skills replace commands with no
loss in Claude Code.

## Acceptance criteria
- **AC1** `commands/{work,review,spec-status,spec-approve,spec-resume}.md` become
  `skills/<same name>/SKILL.md` with the same text, plus `name`, `argument-hint`, and
  `disable-model-invocation: true` (user-invoked only). The body says what to do where
  `$ARGUMENTS` isn't substituted (use what the user typed with the skill). Core's `commands/` is
  removed; packs can still ship commands.
- **AC2** spec-agent (`SKILL.md` role table note and `references/fallback.md`): if `roles/` is
  missing, read `agents/<role>.md` at the package root (`../../agents/` from the skill's folder).
- **AC3** `aicfg apply` on an existing install prunes the old command links and links the new
  skills (checked in a fake HOME); `/work` keeps its name.
- **AC4** A test fails if any core skill or command body uses `$ARGUMENTS` without
  `disable-model-invocation: true` and `argument-hint` (the shape every harness handles), or if
  core ships a `commands/` folder again.
- **AC5** Re-run the real Codex install: the 5 skills are present in the installed copy.
- **AC6** Docs: README plugin section adds the Codex commands, with what Codex gets (skills,
  agents' files, no rules from a plugin, hooks unverified); `docs/harness-packages.md` Codex
  section marked verified where it now is; `docs/formats.md`, `docs/spec-agent.md`, and the README
  layout line say core's slash commands are skills. VERSION 0.3.17; CHANGELOG; `aicfg plugin`.

## Not in this step
Codex hooks and rules (needs a logged-in session; tracked on #50). Agents as Codex TOML roles.

## Open questions
None.
