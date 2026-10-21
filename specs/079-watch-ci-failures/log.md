# 079-watch-ci-failures log

Campaign gh:77 child 2 of 4. Intake 2026-10-21T05:10:55Z: size standard, mode subagent, domains scripting, offline only, delivery normal. Base: 078-pr-status-connector (321 tests OK).

## analyst · spec · done
**Did:** spec.md, 10 ACs, 5 open questions; new living area run-lifecycle + evals block. **Evidence:** engine ran living_specs.py check: exit 0. **Next:** Spec gate.

## engine · spec gate · approved 2026-10-21T13:18:15Z
Recommended answers to Q1-Q5 and the AC9 verification note folded into Open questions.

## architect · plan · done
**Did:** plan.md, 6 tasks in 2 waves; new references/watch.md. **Evidence:** state.json parses. **Open issues:** state schema grows; env var SPEC_PR_STATUS_FIXTURE; sibling-log fixture convention; security triggers: push gating, untrusted CI logs. **Next:** Plan gate.

## engine · plan gate · approved 2026-10-21T14:32:59Z
Wave 1 start: T1, T2, T3.

## implementer · T2 · done
**Did:** references/watch.md (~55 lines; Enter, Fixture hook, Resume pass, CI failure, Push gate); head sha as watch.head_sha. **Evidence:** validate OK; 321 OK (docs only). **Changed files:** skills/spec-agent/references/watch.md **Next:** review (each).

## implementer · T1 · done
**Did:** _field indexes lists on digit segments (out of range/negative -> None); test_state_numeric_index_segment; docs/evals.md note. **Evidence:** red on assertion; 322 OK; validate OK. **Changed files:** scripts/evals.py, tests/test_evals.py, docs/evals.md **Next:** batch review.
- Engine: T2 wrote watch.md in the project root instead of its worktree (scope breach of the worktree rule, file itself in scope); moved into the T2 worktree before review.

## implementer · T3 · blocked
**Did:** state.md: watch object, stage watch, gates.push, post_deliver_retries, metrics.gates.push, gate_rework.push, Resume step 5 → watch.md § Resume pass. **Evidence:** validate fails only on broken links to watch.md (T2's new file, not in T3's worktree); 12 tests fail, unconfirmed. **Next:** engine lands T2 with T3 and re-runs checks. Planning finding: T3 links to a T2 file in the same wave.

## code-reviewer · T2 · changes-requested
**Findings:** HIGH checked_at/head_sha advanced before failure handling (blocked/crashed failures never retried); HIGH no resume rule for pending/rejected Push gate or open C-task; MEDIUM local-clock checked_at vs PR updated_at; MEDIUM summary vs "paths in the log"; MEDIUM external stop scope; LOW base check-run match/pagination; LOW post-push head_sha/checked_at. **Next:** T2 attempt 2.

## implementer · T2 attempt 2 · done
**Did:** all 7 findings fixed (71 lines): resume order C-task → push gate → change check; no-change exit requires every failure recorded; checked_at from pr_status.updated_at, set after the pass; summary lists paths; base match by name; externals recorded then stop. **Evidence:** validate OK; 321 OK. **Next:** re-review.

## code-reviewer · T2 attempt 2 · done
**Findings:** all 7 resolved; no push path bypasses the gate. MEDIUM crash between C-task review and gates.push reset strands commits; LOW mixed external/own "end the pass" wording; LOW set approved before pushing. Engine: no CRITICAL/HIGH, so T2 lands; the MEDIUM and LOWs go to fix task F1 after the batched review.

## engine · wave 1 landed 2026-10-21T14:38:19Z
T1 d8ab616, T2 2b894dd, T3 4626334. Full suite 322 OK, validate OK (T3 broken links cleared). Wave 2 start: T4, T5, T6.

## implementer · T5 · done
**Did:** post-deliver.md status + build step 3 done; watch summary, Push gate, fixture note in spec-agent.md; changelog fragment. **Evidence:** validate OK; 322 OK. **Next:** batch review.

## implementer · T4 · done
**Did:** pointers in SKILL.md (ref link, Deliver step 3, Push gate approval words), lifecycle.md (6b watch row + details), guardrails.md (Push gate only approval for post-deliver push; CI logs untrusted), work/SKILL.md. **Evidence:** validate OK; 322 OK. **Next:** review (each).

## implementer · T6 · done
**Did:** WatchRedCiCaseTest (pass; external fails; approved push fails; log names ticket file); sandbox-005.toml; ticket 008; red-ci.unit-tests.log; README, docs/evals.md. **Evidence:** red: missing case file (compile-only); the two failing-variant tests show the case checks bite (engine accepts as the mutation check); 326 OK; validate OK. **Next:** batch review.
