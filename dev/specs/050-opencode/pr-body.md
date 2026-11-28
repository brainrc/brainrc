## Summary
OpenCode now gets real subagents. Closes #19; step 4 of #50 (refs #50).

**What a real OpenCode 1.18.35 showed:** linking our Claude-format agents into `~/.config/opencode/agents/` breaks the whole OpenCode config. It fails with `Expected object | undefined, got "Read, Grep, ..." tools`, and OpenCode stops loading.

**What `apply` does now:** it renders each agent (core and packs) to `$AICFG_HOME/opencode/agents/<name>.md` and links it from `~/.config/opencode/agents/`. This is turned on by a new `harnesses.toml` key, `agents_format = "opencode"`. Each rendered agent:
- keeps `name`, `description` and the body;
- adds `mode: subagent`;
- turns every tool the agent lacks into a permission `deny`. For example, the read-only code-reviewer gets `edit: deny`. Tools the agent has follow your own OpenCode permissions;
- drops `model`, since Claude tiers don't map to OpenCode's `provider/model-id`, so the subagent uses its caller's model. `mcp__*` tools aren't mapped either. The docs list both as lossy.

`apply` prunes the render and link of a removed agent, and `doctor` flags a stale or missing render, just as it does for `instructions.md`.

**Not in this PR:**
- **An OpenCode guard plugin.** A plugin can block a call, but it can't force a prompt, so "ask before `git push`" would become "deny". That needs its own decision.
- **#19's end-to-end sandbox run.** It needs a model provider login.

## Acceptance criteria
- [x] AC1 render and link via `agents_format`
- [x] AC2 conversion (denies, `mode`, no `model`)
- [x] AC3 prune and doctor
- [x] AC4 tests with a fixture agent; real OpenCode `agent list`
- [x] AC5 docs, VERSION 0.3.19, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK (138). The 6 new tests failed first.
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.
- OpenCode 1.18.35 in a fake home directory after `apply`: `opencode agent list` shows all 9 agents as subagents. Effective denies: analyst `bash`; code-reviewer `edit`; implementer keeps `edit` and `bash`. `doctor` is clean.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
