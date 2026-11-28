# Plan: Campaign ordered-shape fixes from gh:77

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** `campaign.json` gains `delivery` (`sequential` default when absent | `stacked`), `members[].base` (PR base branch, stacked only), `members[].merged` (bool, stacked only), and status `verified`. The `campaign` eval check gains optional `delivery = "stacked"`. New script `skills/spec-agent/scripts/worktree_fence.py` (CLI below).
- **Migrations / data changes:** none (gh:77's campaign.json reads as `sequential`)
- **Security triggers touched:** none (read-only `git status`)
- **Domains:** scripting · **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Docs-driven engine change plus two small stdlib scripts' worth of code. `campaign.md` § Ordered shape gets: status `verified` (child verified, stack Deliver gate not yet presented); the Deliver gate choice `sequential | stacked`; a **Stacked** paragraph (all PRs open at approval, child N's base = child N-1's branch, body template "N of M, stacked on #X. Retarget to `main` before merging."); and one **Retarget rule** shared by both deliveries: before any child PR merges, merge `main` into its branch, re-run tests, and set its base to `main` (on resume, once its predecessor merged; never polled). A **State home** line: `specs/campaign-<slug>/` lives on the child branch in progress; a child's commits change only its own member entry and campaign-level `gates`; `main` is merged in before its PR opens or retargets. `state.md` § Resume lists `verified` and the retarget step.

`worktree_fence.py` (pattern of `active_run.py`: argparse, docstring usage, stdlib): `worktree_fence.py check <worktree> --main <root> --files <glob> ... [--allow <prefix> ...]`. It reads `git -C <worktree> status --porcelain --untracked-files=all` (rename → new path) and fails on any path not matching a `--files` glob (`fnmatch`); it reads `git -C <main> status --porcelain --untracked-files=all` and fails on any path not under an `--allow` prefix (the engine passes `specs/<slug>/`). Prints `STRAY <path>` / `MAIN <path>` per problem, `OK` otherwise; exit 0 / 1, 2 on git error. `efficiency.md` § Parallel waves step 3 and `handoff.md` reference it; every engine status check on a worktree is `git -C <worktree>`.

Eval: `_campaign(project, state, order, delivery)`. `delivery` comes from the check, else `state["delivery"]`, else `sequential` (current logic unchanged). For `stacked`: every member `delivered` with `pr`; member 1's `base` is `main`; member i>1's `base` is member i-1's `branch` or `main`; a member with `merged: true` must have `base` `main` ("merged into <base>, expected main").

## Files
| File | Change |
|---|---|
| `skills/spec-agent/scripts/worktree_fence.py`, `tests/test_worktree_fence.py` | new fence helper + tests (temp git repos) |
| `scripts/evals.py`, `tests/test_evals.py`, `docs/evals.md` | stacked delivery in `campaign` check |
| `skills/spec-agent/references/campaign.md`, `skills/spec-agent/references/state.md`, `docs/spec-agent.md` | verified, delivery choice, stacked, retarget, state home |
| `skills/spec-agent/references/efficiency.md`, `skills/spec-agent/references/handoff.md`, `skills/spec-agent/SKILL.md`, `agents/architect.md` | fence in landing, `git -C`, wave link rule, engine edits after approval |
| `changelog.d/090-campaign-ordered-fixes.md` | fragment, `bump: patch` |

## Risks
- `campaign.md` grows: keep the additions to ~15 lines by replacing the current Release paragraph rather than appending.
- Fence false positives on the engine's own uncommitted state: `--allow specs/<slug>/` covers them.

## Test strategy
AC7 unit tests (pass, stray path, untracked stray, main-tree write, allowed prefix). AC9 tests in `CampaignCheckTest` (stacked pass, stacked merged into non-main fails, bad base fails, absent `delivery` stays sequential). Doc ACs (1-6, 8, 10) by review against this plan. `validate` + unittest each task.

## Tasks
- [ ] **T1** [agent: implementer] `worktree_fence.py check` per the CLI above, with tests
  - files: `skills/spec-agent/scripts/worktree_fence.py`, `tests/test_worktree_fence.py`
  - criteria: AC7
- [ ] **T2** [agent: implementer] Stacked delivery in the `campaign` eval check; docs/evals.md row
  - files: `scripts/evals.py`, `tests/test_evals.py`, `docs/evals.md`
  - criteria: AC9
- [ ] **T3** [agent: implementer] campaign.md § Ordered shape (verified, delivery choice, stacked, retarget rule, state home, schema fields), state.md § Resume, docs/spec-agent.md Campaigns, changelog fragment
  - files: `skills/spec-agent/references/campaign.md`, `skills/spec-agent/references/state.md`, `docs/spec-agent.md`, `changelog.d/090-campaign-ordered-fixes.md`
  - criteria: AC1, AC2, AC3, AC4, AC5
- [ ] **T4** [agent: implementer] Fence + `git -C` in wave landing and dispatch; architect wave link rule; SKILL.md engine edits after approval
  - files: `skills/spec-agent/references/efficiency.md`, `skills/spec-agent/references/handoff.md`, `skills/spec-agent/SKILL.md`, `agents/architect.md`
  - criteria: AC6, AC8, AC10
  - after: T1 (links to `worktree_fence.py`)
