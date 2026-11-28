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

## code-reviewer · batch · changes-requested
2026-10-25T02:13:12Z

**Did:** Fresh-context subagent reviewed 6a586f2..HEAD (specs excluded) against AC1-AC10.

**Evidence:**
- unittest → 365 passed; validate → OK; fence repro: `git mv README.md src/new.md` with `--files 'src/*'` → OK (wrong)

**Changed files:** none

**Findings:**
- HIGH worktree_fence.py:33: rename source path skipped → check it for R entries, add test
- MEDIUM campaign.md:126-129: state home doesn't cover Deliver-gate writes, merged flag, or where resume reads campaign.json → say so
- MEDIUM state.md:163 / campaign.md:166-168: all members verified → resume presents stack Deliver gate
- LOW campaign.md:163: merged parenthetical applies to sequential too → limit to stacked
- LOW evals.py:104: unknown delivery silently sequential → reject
- LOW worktree_fence.py:41: fnmatch `*` crosses `/` → document

**Open issues:** none

**Next:** F1 (scripts), F2 (docs)

## implementer · F1 · done
2026-10-25T02:15:23Z

**Did:** Fence adds a rename's source path (HIGH fixed); docstring notes fnmatch `*` crosses `/` (LOW fixed); campaign eval rejects unknown `delivery` (LOW fixed). Two new tests, red on assertions first.

**Evidence:**
- `python3 -m unittest discover -s tests` → 367 passed

**Changed files:** `skills/spec-agent/scripts/worktree_fence.py`, `tests/test_worktree_fence.py`, `scripts/evals.py`, `tests/test_evals.py`

**Open issues:** none

**Next:** F2

## implementer · F2 · done
2026-10-25T02:15:23Z

**Did:** campaign.md State home names the stack tip from the Deliver gate on (MEDIUM fixed); all-verified resume presents the Deliver gate in campaign.md and state.md (MEDIUM fixed); `merged: true` limited to stacked (LOW fixed).

**Evidence:**
- `python3 scripts/aicfg.py validate` → OK; unittest → OK

**Changed files:** `skills/spec-agent/references/campaign.md`, `skills/spec-agent/references/state.md`

**Open issues:** none

**Next:** re-review fix diff

## code-reviewer · fix re-review · done
2026-10-25T02:17:40Z

**Did:** Re-reviewed be34ac9..HEAD: all 6 findings fixed, no new CRITICAL/HIGH.

## verifier · verify · done
2026-10-25T02:17:40Z

**Did:** Re-ran tests and validate; mapped AC1-AC10 to evidence in verify.md, all pass.

**Evidence:**
- `python3 -m unittest discover -s tests` → 367 passed
- `python3 scripts/aicfg.py validate` → OK

## engine · document · done
2026-10-25T02:17:40Z

**Did:** living_specs apply (campaign-mode, run-lifecycle, evals); pr-body.md, ticket-comment.md drafted. No spec changes after approval.

**Next:** Deliver gate
