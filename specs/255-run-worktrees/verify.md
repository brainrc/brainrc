# Verify: spec-agent: each run in its own git worktree

Run at 2026-10-30T03:42:17Z on commit `b155205`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (plain, and with `XDG_CONFIG_HOME=/home/runner/.config`) | pass: 618 run, 1 skipped, 0 failed (both runs; logs `.runs/test-plain.log`, `.runs/test-xdg.log`) |
| Targeted new tests | `python3 -m unittest discover -s tests -p 'test_run_worktree.py' -v`; `... -p 'test_active_run.py' -v` | pass: 17 passed; 32 passed (`.runs/targeted-run-worktree.log`, `.runs/targeted-active-run.log`) |
| Lint | none configured (`state.json` commands.lint is null) | not configured |
| Build | none configured (`state.json` commands.build is null) | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass: `OK: 26 skills, 9 agents, 0 commands` (`.runs/validate.log`) |
| Plan / diff | none (no infra plan) | not applicable |
| Scripted git sandbox | `bash .runs/e2e255.sh` (temp repo under scratchpad, `env -i` for active_run) | partial: see AC1, AC3, AC7 (`.runs/e2e-sandbox.log`) |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | Model-driven `/work` intake to deliver not run (needs a model). Git-level part: sandbox main HEAD `main`, `status --porcelain` empty before, after `open`, after worktree commit, and after resume; `main has specs/? no` (`.runs/e2e-sandbox.log`). Test `tests/test_run_worktree.py::test_commit_in_worktree_leaves_main_untouched` passes. | not run (end-to-end); git-level partial pass |
| AC2 | `tests/test_run_worktree.py::test_creates_at_default_path_and_prints_only_path` passes; sandbox `open` printed `<tmp>/.brainrc-worktrees/repo/demo` outside main. Recording `state.worktree` is an instruction: `skills/spec-agent/references/state.md` (not re-read; reviewer owns). | pass |
| AC3 | Test `test_commit_in_worktree_leaves_main_untouched` passes; sandbox commit `demo: spec` (`ca6fb19`) is on branch `demo` in the worktree, and main sha unchanged. Stage-by-stage writes under `specs/<slug>/` not exercised (model-driven). | not run (end-to-end); git-level partial pass |
| AC4 | `tests/test_run_worktree.py::test_path_outside_main_and_not_under_tmpdir` and `::test_unittest_discover_in_main_ignores_worktree` pass. | pass |
| AC5 | `tests/test_active_run.py::test_write_worktree_run_dir_records_it` passes; sandbox `write "<wt>/specs/demo"` then pointer file held the worktree path. | pass |
| AC6 | `tests/test_active_run.py::test_read_fallback_finds_newest_run_across_worktrees`, `::test_read_fallback_skips_detached_worktrees`, `::test_read_fallback_without_git_scans_cwd_only` pass; sandbox read with pointer removed from main cwd returned the worktree `specs/demo`. | pass |
| AC7 | Model-driven `/spec-resume` from main not run. Scripted part: after deleting the worktree dir, `open demo --branch demo` (no `--base`) recreated the same path with commit `ca6fb19` present, `specs/demo/state.json` present, and main HEAD/status unchanged (`.runs/e2e-sandbox.log`). Resume instruction: `skills/spec-resume/SKILL.md:12-14`. | not run (end-to-end); git-level partial pass |
| AC8 | `tests/test_run_worktree.py::test_recreates_missing_worktree_from_branch` and `::test_missing_branch_without_base_exits_1_and_creates_nothing` pass. Never fall back to main: `skills/spec-resume/SKILL.md:12-14`. | pass |
| AC9 | Instruction only: `skills/spec-status/SKILL.md:9-10` ("locate each through `state.worktree`... list every run with its stage and worktree path"). | pass (instruction) |
| AC10 | Instruction only: `skills/spec-agent/references/efficiency.md:40-42` (task worktree as `Project root`, `Worktree:` line, run worktree stays clean) and `efficiency.md:44-45` (`worktree_fence.py check <worktree> --main <state.worktree>`). | pass (instruction) |
| AC11 | `tests/test_run_worktree.py::test_main_on_branch_is_refused_and_changes_nothing` passes. | pass |
| AC12 | Instruction only: `skills/spec-agent/references/handoff.md:54` (`Worktree:` line, "also the fallback for harnesses whose subagents take no working directory"); dispatch `Project root` at `handoff.md:45`. | pass (instruction) |

## Notes
- Full suite run twice, both `OK (skipped=1)`, no failures, no flakes observed. The skipped test was not identified (not in scope); baseline_failures is empty.
- The XDG run's log (`.runs/test-xdg.log`) contains a line `Moved ~/.config/ai-config -> ~/.config/brainrc.` from existing code; not investigated.
- Sandbox: `.runs/e2e255.sh` run once in a temp dir under the scratchpad; main checkout at `/home/user/brainrc` was not modified by the scripted checks (only `.runs/` and this file were written there).
- Not run: model-driven `/work` intake to Deliver, interrupt, and `/spec-resume` from main (AC1, AC3, AC7). These need a model and are reported as `not run`, not passing. AC9, AC10, AC12 are checked by instruction citation only, per plan.
- Pass results for AC2, AC4, AC5, AC6, AC8, AC11 rest on unit tests; the sandbox adds corroboration.
