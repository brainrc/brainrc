# 080-watch-review-comments log

Campaign gh:77 child 3 of 4. Intake 2026-10-21T14:54:02Z: size standard, mode subagent, domains scripting, offline only, delivery normal. Base: 079-watch-ci-failures (328 tests OK).

## analyst · spec · done
**Did:** spec.md, 11 ACs, 5 open questions; run-lifecycle (3 ADDED, Push gate MODIFIED), evals (1 ADDED). **Evidence:** engine ran living_specs.py check: exit 0. **Next:** Spec gate.

## engine · spec gate · approved 2026-10-21T15:48:14Z
Recommended answers to Q1-Q5 folded into Open questions.

## architect · plan · done
**Did:** plan.md (79 lines), 6 tasks in 2 waves; review handling in watch.md § Review comments (cap 110 lines). **Open issues:** optional thread id; watch.thread_log[] with hashed keys; no-id replies shown for the user to post. **Next:** Plan gate.

## engine · plan gate · approved 2026-10-21T15:58:11Z
Wave 1 start: T1-T4.

## implementer · T2 · done
**Did:** state.md: review_rounds, threads, thread_log, key rule, no raw text. **Evidence:** validate OK; 328 OK (docs only). **Next:** batch review.

## implementer · T3 · done
**Did:** optional thread id in connectors.md; ticket-github query + mapping emit id; MCP "if present"; reply_thread section (outward, after approved Push gate). **Evidence:** validate OK; 328 OK (docs only). **Next:** review (each).

## implementer · T4 · done
**Did:** WatchReviewCommentCaseTest (pass + 5 failing variants); sandbox-006.toml; injection fixture; ticket 009; PrStatusFixtureTest expects 4 + optional id; README, docs/evals.md. **Evidence:** red on assertions (8 fail, 1 error: missing fixture); 335 OK; validate OK. **Next:** batch review.

## code-reviewer · T3 · changes-requested
**Findings:** HIGH reply_thread missing from ticket-github ops list and MCP table (no honest MCP path); MEDIUM reply_thread missing from connectors.md ops table; LOW overlong line. **Next:** T3 attempt 2.

## implementer · T3 attempt 2 · done
**Did:** reply_thread in ticket-github ops list + table (gh mutation; MCP none: hand draft to user); optional outward row in connectors.md; wrapped line. **Evidence:** validate OK; 328 OK. Engine read the diff: findings resolved; batched review re-covers it.

## implementer · T1 · done
**Did:** watch.md § Review comments; Resume pass R-tasks + new-thread collection; Push gate lists pushes and replies. 110 lines. **Evidence:** validate OK; 328 OK (docs only). **Next:** review (each).
