Run each spec-agent run in its own git worktree

## Why
A `/work` run edited the user's own checkout. A second ticket could not start while an implementer was editing the tree, the engine switched branches under open files, and a stop hook flagged another agent's uncommitted work.

## What changed
- Each run does every stage in its own worktree on the run's branch, at `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`. The main checkout is not touched. A run stops without changes if the checkout has the run's branch checked out.
- `/spec-resume` and `/spec-status` find runs through `state.worktree`. Resume recreates a missing worktree from `state.branch`. If the branch is gone, it stops and says so. It never falls back to the main checkout.
- The run pointer holds the run's path inside its worktree. `active_run.py read` falls back to the newest run in the cwd or in a branch worktree when the pointer is absent or names a missing directory.
- Parallel task worktrees start from the run worktree and land into it. `worktree_fence.py` is unchanged.
- The run's branch, commits, and PR content are unchanged. Harnesses whose subagents take no working directory keep the `Worktree:` dispatch line.

## Acceptance criteria
- [ ] AC1: main checkout unchanged across a run. Not run end to end. Git-level part verified by `test_commit_in_worktree_leaves_main_untouched` and a scripted sandbox run.
- [x] AC2: worktree at the default path, verified by `test_creates_at_default_path_and_prints_only_path`
- [ ] AC3: run files and commits land on the run's branch in the worktree. Not run end to end. Git-level part verified by `test_commit_in_worktree_leaves_main_untouched`.
- [x] AC4: main-checkout test discovery ignores run worktrees, verified by `test_unittest_discover_in_main_ignores_worktree`
- [x] AC5: pointer holds the worktree run path, verified by `test_write_worktree_run_dir_records_it`
- [x] AC6: pointer fallback scans branch worktrees, verified by `test_read_fallback_finds_newest_run_across_worktrees` and `test_read_fallback_skips_detached_worktrees`
- [ ] AC7: `/spec-resume` from the main checkout continues in the worktree. Not run end to end. Git-level recreate verified in a scripted sandbox run.
- [x] AC8: missing worktree recreated from the branch, verified by `test_recreates_missing_worktree_from_branch`
- [x] AC9: `/spec-status` lists each run with its worktree, verified by instruction only (`skills/spec-status/SKILL.md`)
- [x] AC10: wave worktrees nest in the run worktree, verified by instruction only (`skills/spec-agent/references/efficiency.md`)
- [x] AC11: checkout on the run's branch is refused, verified by `test_main_on_branch_is_refused_and_changes_nothing`
- [x] AC12: `Worktree:` dispatch fallback, verified by instruction only (`skills/spec-agent/references/handoff.md`)

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
python3 -m unittest discover -s tests -p 'test_run_worktree.py' -v
python3 -m unittest discover -s tests -p 'test_active_run.py' -v
```
Not yet run: start `/work <ticket>` on a clean checkout. Then `git status --porcelain` and `git rev-parse --abbrev-ref HEAD` in that checkout should match their values from before the run.

## Decisions made without you
- Location: `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`, outside the repo and not under `$TMPDIR`. A `<slug>`-only path would collide between repos that share a parent.
- Setup: the engine installs and copies nothing. It runs the project's configured commands in the worktree. A missing dependency becomes a block that names the cause.
- Checkout already on the run's branch: stop and ask. The engine never switches the user's checkout.
- Missing worktree on resume: recreate it from the branch.
- Pointer fallback: scan `git worktree list`, not only the cwd.
- Harness without subagent working directory: keep the `Worktree:` line as the fallback.
- Wave order: T1 ran alone because it is `review: each`. Then {T2, T4}, then {T3, T5}. The plan had {T1, T2}, {T3, T4}, {T5}.
- **Spec change after approval, for the owner to accept or reject:** AC6 and the run-pointer "Pointer read" requirement now scan branch worktrees only, skipping detached ones. The approved spec said every worktree. Detached task and verify worktrees carry a committed `state.json` with a fresh mtime and could beat the real run.
- T1 incident: while the T1 script was still a stub, a test was committed into the real repo, as a local unpushed commit. The engine undid it with a soft reset (changes kept) and removed the stray file before any push. The tests are now guarded: git refuses any cwd outside the test root, and the worktree path must sit inside that root.

## Follow-ups
- #256: cleanup on merge, and concurrency.
- Not run end to end: the model-driven `/work` run (AC1, AC3) and `/spec-resume` from the main checkout (AC7). The owner decides whether to run them before merge.
- T5 saw one suite failure it could not explain. It did not recur in three engine runs. Likely cause: a stale `.runs/` log (T2 hit the same).
- Review findings: all fixed, none open.

Spec: `specs/255-run-worktrees/spec.md` · Plan: `specs/255-run-worktrees/plan.md`

Part of epic #241 (E23), 1 of 6.
Closes #255

🤖 Generated with [Claude Code](https://claude.com/claude-code)
