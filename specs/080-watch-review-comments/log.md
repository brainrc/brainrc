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
