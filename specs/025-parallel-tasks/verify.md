# Verify: Parallel implement waves in subagent mode

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `references/efficiency.md` § Parallel waves (wave rule, cap 2/3, dispatch in worktrees outside the repo, landing in plan order, measurement); the "Never run writers in parallel" line now points to it | pass |
| AC2 | `SKILL.md` Implement stage opens with the wave rule for `subagent` mode and keeps the per-task loop for everything else | pass |
| AC3 | `templates/plan.md` (`after:` rule and example), `agents/architect.md`, `references/state.md` (4 new rows), `templates/retro.md` Tasks row | pass |
| AC4 | `examples/sandbox/tickets/003-two-features.md`, README row, `evals/cases/sandbox-003.toml` (stage, `metrics.waves.max_width == 2`, verify, tests, both features, default output, main untouched, branch); `test_sandbox_cases_name_tickets_that_exist` red first | pass |
| AC5 | Real run in a scratch sandbox (below) | pass |
| AC6 | VERSION 0.3.13, CHANGELOG; `validate` OK (core and pack); tests OK | pass |

## Real run of the landing steps
Scratch copy of `examples/sandbox`, `TMPDIR` pointed at the scratchpad, three worktrees:
T1 (`farewell.py`, `test_farewell.py`), T2 (`greet.py --version`), T3 (fence `notes.txt`, but
also edits `greet.py`). Main tree stayed clean while they ran. Landing in order: T1 landed
(tests OK, committed, worktree removed), T2 landed, T3 rejected (`stray path: greet.py`, main
tree untouched). Afterwards `greet.py --version` → `greet 1.0`, `greet.py Ada` → `Hello, Ada!`.

The first run found a bug in the note: `git worktree remove` refuses a worktree with staged
changes, which every landed worktree has. Fixed to `--force` (the change is landed and saved
in `.runs/<task>.patch`) and re-run as above.

## Also in this PR
Gates are asked as a multiple-choice question when the harness has one (requested at the
Plan gate): `references/lifecycle.md` § Gate presentation, and `SKILL.md` counts the Approve
button as approval.

## Not verified here
The wall-clock saving needs a subagent-mode run of ticket 003 (issue's third criterion);
proposed as a follow-up after merge.
