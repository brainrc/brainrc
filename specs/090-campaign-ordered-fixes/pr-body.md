Fix ordered-campaign gaps found by the gh:77 run

## Why
In the first ordered campaign (gh:77), the stacked PRs merged into their stacked bases instead of `main`, so three children reached `main` only through an extra PR. The run also hit gaps the procedure doesn't cover: no `verified` member status, no documented stacked delivery, campaign state scattered across branches, same-wave tasks linking each other's new files, implementers writing outside their worktree, and engine edits to approved artifacts with no rule.

## What changed
- `campaign.md` § Ordered shape: the Deliver gate picks `sequential` (default) or `stacked` delivery, recorded as `delivery`. One retarget rule covers both: a child PR merges only with base `main`, after `main` is merged in and its tests re-run. The stacked PR body says to retarget before merging.
- Member status `verified` (built, waiting for the stack Deliver gate), plus `base` and `merged` fields for stacked delivery. Resume skips verified members, and presents the Deliver gate once all of them are verified.
- One home for `campaign.json`: the child branch in progress while building, then the stack tip from the Deliver gate on.
- New `skills/spec-agent/scripts/worktree_fence.py check`: before a wave task lands, every changed worktree path (rename sources included) must match the task's `files`, and the main tree must be clean outside `specs/<slug>/`. Wave landing uses `git -C <worktree>` throughout.
- The architect puts a task that links to or imports another task's new file in a later wave.
- `SKILL.md`: the engine may edit an approved artifact only for wording or path fixes, logged and listed at the Deliver gate.
- `campaign` eval check: `delivery = "stacked"` mode (valid bases, merged only into `main`); an unknown delivery fails.

## Acceptance criteria
- [x] AC1: retarget rule, base `main` before merge, verified by campaign.md § Retarget rule
- [x] AC2: stacked PR body says to retarget, verified by campaign.md § Deliver gate
- [x] AC3: `sequential`/`stacked` chosen at the Deliver gate, recorded as `delivery`
- [x] AC4: status `verified` in campaign.md and state.md § Resume
- [x] AC5: single documented home for `campaign.json` (§ State home)
- [x] AC6: architect wave-link rule, verified by `agents/architect.md`
- [x] AC7: fence helper, verified by `tests/test_worktree_fence.py` (7 tests)
- [x] AC8: fence + `git -C` in wave landing and dispatch (efficiency.md, handoff.md)
- [x] AC9: stacked `campaign` eval, verified by `tests.test_evals.CampaignCheckTest`
- [x] AC10: engine edits after approval rule, in `SKILL.md`

## How to verify
```
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
python3 -m unittest -v tests.test_worktree_fence tests.test_evals.CampaignCheckTest
```

## Follow-ups
- none (all 6 review findings fixed in this PR)

Spec: `specs/090-campaign-ordered-fixes/spec.md` · Plan: `specs/090-campaign-ordered-fixes/plan.md`
Closes #90
