# Plan: spec-agent: each run in its own git worktree

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** `active_run.py read` also scans `git worktree list` when the pointer is missing or stale (more results, same output format). The pointer now names `<worktree>/specs/<slug>`. `state.json` gains an additive `worktree` field. New script `run_worktree.py`. Affects external tools that read the pointer, and in-flight runs: a run with no `worktree` gets one on resume, so a user whose checkout is on that branch is told to switch (AC11).
- **Migrations / data changes:** none
- **Security triggers touched:** none (git subprocess calls use argument lists)
- **Domains:** scripting
- **Environments affected on deploy:** none (the engine docs ship through `brainrc apply`)
- **Destructive or replacing changes:** none

## Approach
New stdlib helper `skills/spec-agent/scripts/run_worktree.py open <slug> --branch <b> [--base <base>]`, in the style of `worktree_fence.py` (argparse, `subprocess.run` with argument lists, `main() -> int`). It finds the main checkout from the first entry of `git worktree list --porcelain`, so it works from inside any worktree. The path is `<main parent>/.brainrc-worktrees/<main name>/<slug>`. It exits 1 and changes nothing when the main checkout has `<b>` checked out; the message names the branch and the fix (`git -C <main> switch <other branch>`). If a worktree on `<b>` already exists at that path, it prints the path. If the path is missing, it runs `git worktree prune` and recreates the worktree from `<b>`. If `<b>` does not exist, it creates the branch from `--base` (intake); with no `--base` (resume) it exits 1 instead of falling back. Exit 2 means git failed. stdout is only the absolute path. The engine records that path as `state.worktree`, whichever tool made the worktree, so native harness tools and plain git give the same value.

`active_run.py read` keeps the pointer branch unchanged. Its fallback goes from `Path("specs").glob` to the `specs/*/state.json` of cwd plus every worktree path from `git worktree list --porcelain` (with a timeout; git errors mean cwd only), deduped by resolved path, newest by mtime. `write` stays as it is: callers pass `<worktree>/specs/<slug>`.

Engine docs: intake step 4 calls `open` with `--base` instead of creating the branch. From then on, `Project root` and every git command use `state.worktree`. Resume calls `open` without `--base`. Waves use `git -C <run worktree> worktree add`, pass `--main <run worktree>`, and apply in the run worktree. Every dispatch now carries the `Worktree:` line, because subagent cwd is the main checkout. Design choice: one helper instead of prose git steps, so the refusal and recreate cases (AC8, AC11) can be unit-tested.

## Files
| File | Change |
|---|---|
| `skills/spec-agent/scripts/run_worktree.py` | new: `open` subcommand |
| `tests/test_run_worktree.py` | new: temp-git-repo tests |
| `skills/spec-agent/scripts/active_run.py`, `tests/test_active_run.py` | modify: worktree-aware fallback in `read`, docstring |
| `skills/spec-agent/SKILL.md`, `references/lifecycle.md`, `references/state.md` | modify: intake, Run step 1, `worktree` field, Resume, checkpoint and pointer paths |
| `references/efficiency.md`, `references/handoff.md`, `references/watch.md` | modify: waves nested in the run worktree, `Worktree:` on every dispatch, post-merge runs from the run worktree |
| `skills/spec-resume/SKILL.md`, `skills/spec-status/SKILL.md` | modify: locate runs through the pointer, `state.worktree`, and the worktree scan; status shows the worktree path |
| `docs/spec-agent.md`, `docs/e2e-runs.md`, `changelog.d/255-run-worktrees.md` | modify/new: user docs, fallback note (Open question 6), fragment |

## Risks
- During a wave, a detached task worktree's copy of `state.json` could be the newest in the fallback scan. Mitigation: the pointer is written at intake and on resume, so the fallback runs only when the pointer is gone. Listed in docs; the spec rule is kept word for word.
- A harness sandbox may deny writes outside the repo. Mitigation: `docs/e2e-runs.md` names `--add-dir <repo parent>/.brainrc-worktrees`.
- Context bloat in loaded references. Mitigation: each doc task adds at most about 15 net lines, and the git detail lives in the script.

## Test strategy
Unit tests use temporary git repos (`git init`, `-c user.name/email`, no network):
- `tests/test_run_worktree.py` proves AC2 (default path, created at intake), AC4 (path is outside the main toplevel and not under `$TMPDIR`; `unittest discover` in main finds no worktree test), AC8 (recreate from the branch; a missing branch exits 1 with no worktree), and AC11 (exit 1, worktree list and main status unchanged). It also covers the git mechanics of AC1/AC3: commit in the worktree, then main HEAD and `status --porcelain` are unchanged and the commit is on the branch.
- `tests/test_active_run.py` proves AC5 (writing a worktree run dir records it) and AC6 (scan finds the newest run across worktrees; no git means cwd only).
- AC9, AC10, and AC12 are proven only by the instruction changes (T3–T5), checked by the reviewer against the quoted rules.
- AC1, AC3, and AC7 end to end: the verifier states this step. In a sandbox repo per `docs/e2e-runs.md`, run `/work` to the Deliver gate, interrupt it and `/spec-resume` from main, and diff main's HEAD/status before and after. If it isn't run, report it as `not run`, never as passing.

## Tasks
- [ ] **T1** [agent: implementer] `run_worktree.py open`: path, create, recreate, refuse
  - files: `skills/spec-agent/scripts/run_worktree.py`, `tests/test_run_worktree.py`
  - criteria: AC2, AC4, AC8, AC11 (mechanics of AC1, AC3)
  - review: each
- [ ] **T2** [agent: implementer] `active_run.py read` scans `git worktree list`
  - files: `skills/spec-agent/scripts/active_run.py`, `tests/test_active_run.py`
  - criteria: AC5, AC6
- [ ] **T3** [agent: implementer] Intake, Run, state, and Resume use the run worktree
  - files: `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/lifecycle.md`, `skills/spec-agent/references/state.md`
  - criteria: AC1, AC2, AC3, AC5, AC7, AC8, AC11
  - after: T1
- [ ] **T4** [agent: implementer] Waves and dispatch nested in the run worktree
  - files: `skills/spec-agent/references/efficiency.md`, `skills/spec-agent/references/handoff.md`, `skills/spec-agent/references/watch.md`
  - criteria: AC10, AC12, AC1
- [ ] **T5** [agent: implementer] `/spec-resume`, `/spec-status`, user docs, changelog fragment
  - files: `skills/spec-resume/SKILL.md`, `skills/spec-status/SKILL.md`, `docs/spec-agent.md`, `docs/e2e-runs.md`, `changelog.d/255-run-worktrees.md`
  - criteria: AC7, AC8, AC9
  - after: T1, T2

Waves: {T1, T2} → {T3, T4} → {T5}. T4 has no code dependency and may run in the first free slot.
