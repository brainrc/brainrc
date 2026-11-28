# Plan: watch post-merge verify and the retro's After delivery section

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none (stdlib only).
- **Public API / contract changes:** `pr_status` gains two optional fields, `merged_at` and `merge_commit_sha` (additive; `ticket-github` maps `mergedAt`/`mergeCommit`). `retro_report.py --json` gains run fields and aggregate counts; `schema_version` 1 → 2 (AC8).
- **Migrations / data changes:** none. New optional `state.json` fields; old runs read as `unknown`.
- **Security triggers touched:** none from the checklist. The post-merge checkout is a guardrail: clean tree required, detached worktree, never force/push/open anything (T1, `review: each`).
- **Domains:** scripting · **Environments affected on deploy:** none · **Destructive or replacing changes:** none

## Approach
Engine prose: `watch.md` § Resume pass step 3 sends `merged`/`closed` to a new `## Merged or closed`
section, replacing the "reported only" lines (header line 5, step 3). It reuses the verifier and
`templates/verify.md` for `verify-merged.md`, resume's clean-tree rule (`state.md` § resume) and
`retro.md` from Deliver. Merge sha: `merge_commit_sha` when `git cat-file -e <sha>^{commit}`
resolves, else the local tip of `state.base`, stated in the file. Verify in a detached worktree
under `.runs/` (`git worktree add --detach`, then `git worktree remove`) so the user's checkout is
never touched. Order: verify file + `watch.*` fields, `metrics.time_to_merge`, append
`## After delivery` (skip if present), then `stage: done` last, so a crash re-runs safely.
`time_to_merge` = `merged_at − pr_opened_at` in minutes, unset if either is missing or the
difference is negative. `SKILL.md` Deliver step 2 sets `metrics.pr_opened_at` from `date -u`.
Expected `watch.md` length: about 138 lines (under the ~140 limit).

Rollup: extend `retro_metrics.RunRecord` and `load_run` (reusing `_int`, `_num`, `_dict`) with
`outcome`, `post_merge`, `time_to_merge`, `review_rounds`, `ci_failures` (count of
`watch.ci_failures`); only known enum values count, else `None`. `retro_aggregate`: add
`time_to_merge` to `OTHER_METRICS` and an `outcomes` dict `{merged, abandoned, regression}` per
group. `retro_report._run_row`/`render_markdown`: run columns `Outcome`, `Post-merge`,
`Time to merge`, `Review rounds`, `CI failures` (after `Criteria`); aggregate columns
`Avg time to merge`, `Merged`, `Abandoned`, `Regressions`. Missing values render `unknown` via `_fmt`.
Eval: a new case reuses existing `state`/`file` check kinds; `evals.py` is unchanged.

## Files
| File | Change |
|---|---|
| `skills/spec-agent/references/{watch,state,lifecycle}.md`, `SKILL.md`, `templates/retro.md` | modify: post-merge, outcome, new fields, After delivery skeleton |
| `skills/spec-agent/references/connectors.md`, `skills/ticket-github/SKILL.md` | modify: optional `merged_at`, `merge_commit_sha` |
| `examples/sandbox/pr_status/merged.json` | modify (additive): `merged_at`, `merge_commit_sha` |
| `scripts/retro_{metrics,aggregate,report}.py` + tests | modify: new fields, counts, columns, schema 2 |
| `evals/cases/sandbox-007.toml`, `examples/sandbox/tickets/010-watch-merged.md` | new |
| `examples/sandbox/README.md`, `tests/test_evals.py` | modify |
| `docs/{efficiency,roadmap,post-deliver,spec-agent}.md`, `changelog.d/081-watch-post-merge.md` | modify / new |

## Risks
- A live sandbox run has no PR, so no `pr_opened_at`, so `time_to_merge` stays unset; mitigated by grading sandbox-007 on a synthetic run folder (spec Open question 1), said in the case comment.
- `Total min` (start → done) now includes merge wait, and `STAGES` lacks `watch`; out of scope, noted as a follow-up.
- Same-wave edits to a shared file (080 lesson); mitigated by disjoint `files` and `tests/test_evals.py` serialized T2 → T4.

## Test strategy
AC8: unit tests first in `tests/test_retro_{metrics,aggregate,report}.py` (known, missing, wrong-type, 0 vs unknown). AC9: `WatchMergedCaseTest` in `tests/test_evals.py` (pass plus one failing variant per check), fixture shape test accepts the optional keys. AC1–AC7, AC10: prose, checked by review against the spec and `aicfg validate`.

## Tasks
- [ ] **T1** [agent: implementer] Engine: `## Merged or closed` in watch.md, state/lifecycle fields, `pr_opened_at` at link_pr, retro skeleton
  - files: `skills/spec-agent/references/watch.md`, `skills/spec-agent/references/state.md`, `skills/spec-agent/references/lifecycle.md`, `skills/spec-agent/SKILL.md`, `skills/spec-agent/templates/retro.md`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC10 · review: each · wave 1
- [ ] **T2** [agent: implementer] Optional `merged_at`/`merge_commit_sha` in pr_status contract, gh mapping, merged fixture
  - files: `skills/spec-agent/references/connectors.md`, `skills/ticket-github/SKILL.md`, `examples/sandbox/pr_status/merged.json`, `tests/test_evals.py`
  - criteria: AC2, AC9 · review: each · wave 1
- [ ] **T3** [agent: implementer] RunRecord outcome, post_merge, time_to_merge, review_rounds, ci_failures (test first)
  - files: `scripts/retro_metrics.py`, `tests/test_retro_metrics.py`
  - criteria: AC6, AC8 · review: batch · wave 1
- [ ] **T4** [agent: implementer] Sandbox eval for the merged path
  - files: `evals/cases/sandbox-007.toml`, `examples/sandbox/tickets/010-watch-merged.md`, `examples/sandbox/README.md`, `tests/test_evals.py`
  - criteria: AC9 · review: batch · wave 2 · after: T2
- [ ] **T5** [agent: implementer] Aggregate counts, report columns, schema_version 2 (test first)
  - files: `scripts/retro_aggregate.py`, `scripts/retro_report.py`, `tests/test_retro_aggregate.py`, `tests/test_retro_report.py`
  - criteria: AC8 · review: batch · wave 2 · after: T3
- [ ] **T6** [agent: implementer] Docs, roadmap Done, changelog fragment (`bump: patch`)
  - files: `docs/efficiency.md`, `docs/roadmap.md`, `docs/post-deliver.md`, `docs/spec-agent.md`, `changelog.d/081-watch-post-merge.md`
  - criteria: AC8, AC10 · review: batch · wave 2 · after: T1, T3
