## Summary
In subagent mode, spec-agent can now run independent plan tasks in parallel. Refs #25, which stays open until a real run measures the time saved.

- **Waves:** pending tasks whose `after:` dependencies are done and whose `files` don't overlap. At most 2 per wave for `standard` size, and 3 for `large`. Test-writer tasks and `review: each` tasks run alone.
- **Isolation:** each parallel task runs in its own `git worktree`, created outside the repo, so implementers never run tests against each other's half-finished changes.
- **Landing, in plan order:** stage the worktree's changes, check they stay inside the task's `files`, save a patch to `.runs/`, `git apply --index` it to the main tree, run the scoped tests, and commit. A stray path or a patch that won't apply is a failed attempt; that task retries alone and the others still land.
- **State and retro:** `tasks[].wave`, `.worktree` and the start and finish times, plus `metrics.waves` with task-minutes against wall-clock minutes. The retro's Tasks row shows the time saved.
- **Plans:** an optional `after: T1` line, documented in the plan template and the architect agent.
- **Sandbox:** ticket 003 has two independent slices, and `evals/cases/sandbox-003.toml` checks for a wave of width 2. A new test checks that every eval case names a ticket that exists.
- **Also, requested during this run:** gates are now asked as a multiple-choice question (Approve, Request changes, plus any open choices) when the harness has one, such as `AskUserQuestion` in Claude Code.

## Acceptance criteria
- [x] AC1 design note in `references/efficiency.md`
- [x] AC2 Implement stage runs and lands waves
- [x] AC3 `after:`, state fields, retro line
- [x] AC4 sandbox ticket 003 and its eval case
- [x] AC5 landing steps tested for real
- [x] AC6 VERSION 0.3.13, CHANGELOG
- [ ] Issue criterion 3, the measured time saving: needs a real subagent-mode run of ticket 003, to come in a follow-up

## Testing
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` and `validate --pack examples/pack-acme` → OK
- Real run in a scratch sandbox: two tasks landed in order from separate worktrees, and a third task's stray edit was rejected. The run found that `git worktree remove` refuses a worktree with staged changes; the note now uses `--force`, which is safe because the change is already landed and saved as a patch.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
