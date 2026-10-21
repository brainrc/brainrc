## analyst · spec stage · done
2026-10-21

**Did:** spec.md: 14 criteria; decisions (owner answer: build all, one Deliver gate, PRs one at a time; local `depends_on:` frontmatter); new areas campaign-mode, ticket-connectors; MODIFIED run-pointer.

**Evidence:** engine living_specs check exit 0.

**Changed files:** `specs/074-campaign-ordered-shape/spec.md`

**Open issues:** 4 questions (merge detection, GitHub depends-on via gh/MCP, --shape ordered without links, eval reach into children).

## analyst · record gate answers · done
2026-10-21

**Did:** Decisions recorded; AC15 merge detection on resume, AC16 GitHub dependency source + body fallback, AC17 --shape ordered without links, AC18 campaign eval check; new area evals. Open questions: None.

**Evidence:** 18 criteria; engine living_specs check exit 0.

## architect · plan · done
2026-10-21

**Did:** 6 tasks: T1 evals campaign kind; T2 connector dependencies op; T3 campaign.md + SKILL.md + work skill; T4 state.md resume; T5 sandbox epic + sandbox-004 (after T1); T6 docs + fragment. Shared shapes pinned in Approach.

**Changed files:** `specs/074-campaign-ordered-shape/plan.md`

**Open issues:** contract additions (optional dependencies op, campaign.json fields, campaign eval kind).

## implementer · T1 · done
2026-10-21

**Did:** `campaign` check kind, `find_campaign`, `cmd_check` fallback, per the pinned Eval shape; 8 tests.

**Evidence:** red 7 failures + 1 error; full suite 314 OK; validate OK (worktree).

**Changed files:** `scripts/evals.py`, `tests/test_evals.py`

**Open issues:** docs/evals.md needs a campaign row (added to T6's files).

## implementer · T2 · done
2026-10-21

**Did:** optional read-only `dependencies` op (pinned shape) in connectors.md; ticket-local `depends_on:`/`children:`; ticket-github API blocked_by, `Depends on #N` body fallback (numbers only), sub_issues order, read-only PR merge check, MCP equivalents.

**Evidence:** validate OK; full suite 306 OK (worktree). Doc-only.

## engine · wave 1 · landed
2026-10-21

T1, T2 landed in order. metrics.waves: width 2, 3.5 task-min in 1.9 wall-min (T1's finished_at recorded at landing, about a minute late).

## implementer · T3 · done
2026-10-21

**Did:** campaign.md shape detection, --shape, waiting status, gate line (shape/order/source), `## Ordered shape` section (pinned shapes, Kahn order, cycle/out-of-epic stop, per-child gates, branch chaining, stack Deliver gate, release, propagation, pause, pull-only merges); SKILL.md Run step 1 trigger; work skill --shape and campaign resume.

**Evidence:** validate OK; full suite 314 OK (worktree). Doc-only.

## implementer · T4 · done
2026-10-21

**Did:** state.md Resume paragraph for waiting members (read-only PR state or user "merged", never poll, rules in campaign.md § Ordered shape); pointer names the child in progress.

**Evidence:** validate OK; full suite 314 OK (worktree).

## engine · wave 2 · landed
2026-10-21

T3, T4 landed; cross-reference `campaign.md § Ordered shape` resolves. metrics.waves: 2 waves, 5.4 task-min in 3.0 wall-min.
