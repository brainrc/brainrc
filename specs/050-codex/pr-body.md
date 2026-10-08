## Summary
Codex can now install ai-config from the existing plugin. Step 2 of #50; refs #50.

```text
codex plugin marketplace add bxker/ai-config
codex plugin add ai-config@ai-config
```

**A real install with Codex 0.161.0 found two problems, both fixed here:**
1. **Codex skips commands that use `$ARGUMENTS`,** so none of our 5 arrived. Core's `/work`, `/review`, `/spec-status`, `/spec-approve` and `/spec-resume` are now **user-invoked skills**: `git mv` to `skills/<name>/SKILL.md`, adding `argument-hint` and `disable-model-invocation: true`.
   - In Claude Code they keep their names, since a skill is invoked as `/<name>` and `$ARGUMENTS` works in it.
   - Where `$ARGUMENTS` isn't filled in, a line in each skill tells the model to use what the user typed.
   - On an existing install, `apply` removes the old command links and links the skills.
   - Packs can still ship `commands/`.
2. **Codex's install copy drops symlinks,** so `skills/spec-agent/roles` disappears. spec-agent now reads `../../agents/<role>.md` when `roles/` is missing.

A new test keeps every argument-taking skill user-invoked and stops core's `commands/` from coming back. The docs cover the Codex install (README), mark the Codex findings as verified (`docs/harness-packages.md`), and are updated in `docs/formats.md`, `docs/spec-agent.md` and AGENTS.md. `VERSION` 0.3.17.

**Not verified:** whether Codex runs the plugin's guard hooks, and how it would load rules. Both need a logged-in Codex session. The README says so.

## Acceptance criteria
- [x] AC1 commands become user-invoked skills; core `commands/` removed
- [x] AC2 spec-agent `roles/` fallback
- [x] AC3 `apply` upgrade swaps command links for skills (real run)
- [x] AC4 test
- [x] AC5 real Codex reinstall shows the 5 skills
- [x] AC6 docs, VERSION, CHANGELOG, plugin manifests

## Testing
- `python3 -m unittest discover -s tests -q` → OK. The new test failed first.
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.
- Codex 0.161.0, installed into a scratch folder with a fake home, before and after this change: the plugin installs, and after the change the five skills are present.
- Upgrading an existing `aicfg` install in a fake home directory: old command links removed, skills linked, `doctor` clean.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
