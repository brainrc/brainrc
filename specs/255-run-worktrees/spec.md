# Spec: spec-agent: each run in its own git worktree

Ticket: gh:255 · Size: standard · Status: draft

## Problem
A `/work` run edits the user's own checkout. A second ticket cannot start while an implementer is editing the tree, the engine switches branches under the user's open files, and a stop hook flags another agent's uncommitted work. Worktrees exist today only inside a run (parallel waves, post-merge verify), so the run itself gives the user no isolation.

## Goals
- A run does every stage in its own worktree on the run's branch; the main checkout is never touched.
- Tools that find runs (pointer, `/spec-resume`, `/spec-status`) work through the recorded worktree.
- The run's branch, commits, and PR are unchanged.

## Non-goals
- Changing `worktree_fence.py`, the PR flow, or branch naming.
- Installing dependencies or building environments for the user (see Open question 2).
- Cleaning up a worktree after merge beyond what the run already removes (task and verify worktrees).

## Acceptance criteria
- **AC1**: Given a sandbox repo on branch `main` with a clean status, when a `/work` run goes intake to deliver, then `git rev-parse --abbrev-ref HEAD` and `git status --porcelain` in the main checkout are identical before and after, and no tracked or untracked file there changed.
- **AC2**: Given a new run, when intake finishes, then a worktree for `state.branch` exists outside the main checkout's working tree at the default location, and `state.json` records its absolute path as `worktree`.
- **AC3**: Given a run with `worktree` set, when any stage writes `specs/<slug>/` or commits, then those files and commits are in the run worktree on the run's branch, and the branch and PR content match a run without worktrees.
- **AC4**: Given the run worktree's parent directory, when the project's test command runs in the main checkout, then it finds no test files from any run worktree.
- **AC5**: Given a run with `worktree` set, when `active_run.py write` is called, then the pointer holds the absolute path of `<worktree>/specs/<slug>`.
- **AC6**: Given the pointer is absent or names a missing directory and cwd is the main checkout, when `active_run.py read` runs, then it returns the newest run found in `<cwd>/specs/` or in any worktree listed by `git worktree list`, by `state.json` mtime.
- **AC7**: Given an interrupted run whose worktree exists, when `/spec-resume` runs from the main checkout, then it finds the run through `state.worktree`, continues in the worktree, and leaves the main checkout unchanged.
- **AC8**: Given `state.worktree` names a path that no longer exists, when `/spec-resume` runs, then it recreates the worktree from `state.branch` if the branch exists, else stops and says so; it never falls back to the main checkout.
- **AC9**: Given runs in two worktrees, when `/spec-status` runs, then it lists both with their stage and worktree path.
- **AC10**: Given a parallel wave, when tasks are dispatched, then each task worktree is created from the run worktree's HEAD, `worktree_fence.py check` is called with the run worktree as `--main`, and landing patches apply in the run worktree.
- **AC11**: Given the main checkout already has `state.branch` checked out, when a run starts or resumes, then the engine stops with a message naming the branch and the fix, and changes nothing.
- **AC12**: Given a harness whose subagents take no working directory, when a task is dispatched, then the prompt passes the worktree as `Project root` with the `Worktree:` instruction as before.

## Constraints
- Stdlib-only Python 3.11+ for `active_run.py`; offline-testable with temporary git repos.
- No absolute user paths or secrets committed to docs; examples use `~` and acme.
- Where the harness has native worktree tools, they are used; else plain `git worktree`. Both give the same recorded `worktree`.

## Requirement changes

### Area: run-pointer
#### MODIFIED: Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to
`active-run` in the settings home (default `~/.config/brainrc/active-run`) at intake, on every
resume, and on every checkpoint commit (each gate, block, and done), creating the directory if
needed, via `skills/spec-agent/scripts/active_run.py write`. The run directory SHALL be the
`specs/<slug>` inside the run's worktree. A write failure SHALL warn on stderr and exit 0. In an
ordered campaign the pointer SHALL name the child currently in progress. (AC5)
#### MODIFIED: Pointer read
`active_run.py read` SHALL return the pointer's run if the file exists and names an existing
directory, else the newest run by `state.json` mtime among `<cwd>/specs/` and the `specs/` of every
worktree listed by `git worktree list`. (AC6)

### Area: run-lifecycle
#### ADDED: Run worktree
A run SHALL do every stage in its own git worktree on the run's branch, record its absolute path as
`state.json` `worktree`, and SHALL NOT change the main checkout's branch, index, or files. It SHALL
stop without changes if the main checkout has the run's branch checked out. (AC1, AC2, AC3, AC4, AC11)
#### ADDED: Resume through the worktree
`/spec-resume` and `/spec-status` SHALL locate runs through `state.worktree`, continue in that
worktree, and recreate it from `state.branch` when missing, never falling back to the main
checkout. (AC7, AC8, AC9)
#### ADDED: Nested wave worktrees
Parallel task worktrees SHALL be created from the run worktree and landed into it, with
`worktree_fence.py` unchanged. Harnesses whose subagents take no working directory SHALL keep the
`Project root` plus `Worktree:` dispatch. (AC10, AC12)

## Open questions
1. Location. *Why: wiped or in-repo paths lose work or confuse test runners.* Default: `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`, outside the repo and not under `$TMPDIR`; the ticket's `<slug>`-only path would collide between repos sharing a parent.
2. Per-worktree setup (venv, installs). *Why: time and disk versus a failing first test run.* Default: the engine installs nothing and copies nothing; it runs the project's configured commands in the worktree, and a missing-dependency failure becomes a block naming the cause.
3. Main checkout already on the run's branch. *Why: git refuses a second worktree on it.* Default: stop and ask the user to switch their checkout (AC11); never switch it for them.
4. Missing worktree on resume. *Why: a deleted directory should not lose or redirect a run.* Default: recreate from the branch (AC8).
5. Pointer fallback scan of other worktrees (AC6). *Why: a `specs/` scan of the main checkout no longer sees runs.* Default: scan `git worktree list`.
6. Harness without subagent working directory. *Why: isolation depends on it.* Default: keep the `Worktree:` workaround (AC12); docs/e2e-runs.md notes it as the fallback, not the norm.
