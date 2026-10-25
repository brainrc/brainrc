# Log: 090-campaign-ordered-fixes

## engine · intake · done
2026-10-25T00:47:47Z

**Did:** Branch from main (e76f01c), ticket.md from gh:90, commands discovered. Size standard, mode fallback (named agents not installed), domains: scripting.

**Evidence:**
- `python3 -m unittest discover -s tests` → 353 passed
- `python3 scripts/aicfg.py validate` → OK: 26 skills, 9 agents, 0 commands

**Changed files:** `specs/090-campaign-ordered-fixes/ticket.md`, `state.json`

**Open issues:** none

**Next:** spec stage

## analyst · spec · done
2026-10-25T00:49:42Z

**Did:** Wrote spec.md: 10 criteria, delta to campaign-mode, run-lifecycle, evals.

**Evidence:**
- `living_specs.py check spec.md` → would update 3 areas, exit 0

**Changed files:** `specs/090-campaign-ordered-fixes/spec.md`

**Open issues:** 2 open questions (campaign.json home; worktree guard form)

**Next:** Spec gate

## engine · spec gate · approved
2026-10-25T02:02:18Z

**Did:** Spec approved. Open questions resolved: campaign.json on the child branch in progress; engine-run worktree_fence.py, not a hook.

## architect · plan · done
2026-10-25T02:02:18Z

**Did:** plan.md with 4 tasks (T1 fence script, T2 eval stacked, T3 campaign docs, T4 landing/architect/SKILL.md).

**Evidence:**
- read-only inspection of campaign.md, evals.py, test_evals.py, active_run.py

**Changed files:** `specs/090-campaign-ordered-fixes/plan.md`

**Open issues:** callouts: campaign.json fields `delivery`, `members[].base`, `members[].merged`, status `verified`; new script CLI.

**Next:** Plan gate

## engine · plan gate · approved
2026-10-25T02:03:58Z

## implementer · T1 · done
2026-10-25T02:03:58Z

**Did:** Added worktree_fence.py check (git -C status -z, fnmatch on files, main-tree allow prefixes) with 6 tests; red shown against a stub (4 assertion failures).

**Evidence:**
- `python3 -m unittest tests.test_worktree_fence` → 6 passed
- `python3 -m unittest discover -s tests` → 359 passed

**Changed files:** `skills/spec-agent/scripts/worktree_fence.py`, `tests/test_worktree_fence.py`

**Open issues:** none

**Next:** T2

## implementer · T2 · done
2026-10-25T02:05:12Z

**Did:** `campaign` check takes `delivery` (check, else campaign.json, else sequential); stacked rules for base/merged; 6 tests (5 red on assertions first); docs/evals.md row.

**Evidence:**
- `python3 -m unittest tests.test_evals` → 68 passed
- `python3 -m unittest discover -s tests` → OK

**Changed files:** `scripts/evals.py`, `tests/test_evals.py`, `docs/evals.md`

**Open issues:** none

**Next:** T3

## implementer · T3 · done
2026-10-25T02:07:13Z

**Did:** campaign.md § Ordered shape: `delivery`, `base`, `merged`, status `verified`, State home, Deliver gate delivery choice, stacked body template, Retarget rule, merge detection and resume updates; state.md § Resume; docs/spec-agent.md; changelog fragment.

**Evidence:**
- `python3 scripts/aicfg.py validate` → OK
- `python3 -m unittest discover -s tests` → OK

**Changed files:** `skills/spec-agent/references/campaign.md`, `skills/spec-agent/references/state.md`, `docs/spec-agent.md`, `changelog.d/090-campaign-ordered-fixes.md`

**Open issues:** campaign.md is now 168 lines (+15).

**Next:** T4

## implementer · T4 · done
2026-10-25T02:08:18Z

**Did:** efficiency.md wave rule (linked tasks wait) and landing (fence first, `git -C <worktree>`); handoff.md Worktree line; architect.md wave link rule; SKILL.md engine edits after approval.

**Evidence:**
- `python3 scripts/aicfg.py validate` → OK
- `python3 -m unittest discover -s tests` → OK

**Changed files:** `skills/spec-agent/references/efficiency.md`, `skills/spec-agent/references/handoff.md`, `skills/spec-agent/SKILL.md`, `agents/architect.md`

**Open issues:** none

**Next:** batched review
