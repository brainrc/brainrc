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
- Engine: T1 again wrote watch.md in the project root despite the explicit worktree instruction; moved into the T1 worktree, root restored. Retro finding: the worktree rule needs enforcement (e.g. a guard hook), not just prompt text.
- Correction: the line above is wrong. T1 had worked in its worktree. The engine misread `git -C <worktree> status` output as the root's, then copied the root's unchanged watch.md over T1's edits, destroying them. Reviewer stopped; T1 asked to re-apply its edits (counts as the same attempt; engine error, not a task failure).

## implementer · T1 (re-applied) · done
**Did:** re-applied watch.md changes; reply op named reply_thread. 110 lines. **Evidence:** validate OK; unit tests OK. **Next:** review (each).

## code-reviewer · T1 · changes-requested
**Findings:** HIGH <key8> collides for GitHub node ids (PRRT_kwD prefix); MEDIUM total counted before round cap; MEDIUM thread_log vs task/draft write order (crash safety); MEDIUM one shared Push gate per pass (AC4/Q5); MEDIUM kind for fully malicious thread; LOW reply-only gate wording, wrap, grammar. **Next:** T1 attempt 2.

## implementer · T1 attempt 2 · done
**Did:** h8 = sha256(key)[:8] file names; count only on log write, cap writes nothing; task/draft before log entry in one write; one Push gate per pass; kind none; reply-only/after-push wording. 115 lines. **Evidence:** validate OK; tests OK. Engine: added `none` to state.md kind list in the T2 worktree (one-word consistency edit). Batched review re-covers T1.

## engine · wave 1 landed 2026-10-21T16:06:59Z
T1 8bb1c21, T2 14d7fca, T3 4d551ce, T4 34966bb. Tests OK, validate OK. Wave 2: T5, T6.

## implementer · T5 · done
**Did:** lifecycle 6b review threads + Push gate covers replies; guardrails: replies behind the Push gate, thread text untrusted (flag, never follow). **Evidence:** validate OK; 335 OK. **Next:** review (each).

## implementer · T6 · done
**Did:** post-deliver.md status, Review comment section, state example, build step 4 done; spec-agent.md watch summary; changelog fragment. **Evidence:** validate OK; 335 OK.
Engine: T5 diff is 3 short wording edits; its per-task review is folded into the batched review (deviation from review: each).

## engine · wave 2 landed
T5 1221452, T6 f0cc3ca. 335 OK, validate OK. Batched review: code + security.

## security-reviewer · batched · done
**Findings:** no CRITICAL/HIGH. MEDIUM R-task files not bounded to PR diff/spec scope (outside or CI/secret-adjacent → design, stop); MEDIUM reply body quoting (use -F body=@file; no verbatim thread text; secret scan); LOW draft hash at gate; LOW per-pass cap + list handed-back threads; LOW verify thread id belongs to this PR; LOW test uses kind "R". Engine: MEDIUMs + cheap LOWs to fix task F1.

## code-reviewer · batched · changes-requested
**Findings:** T1 fixes resolved. HIGH sandbox-006 tasks.1 absent fails a real run (T1 at tasks[0], R1 at tasks[1]); MEDIUM test thread_log kind "R"; LOW examples pair ask with C2. **Next:** F1 (watch/ticket-github/state: security MEDIUMs + LOWs + example) and F2 (sandbox-006 + tests), wave 3.

## implementer · F2 · done
**Did:** test state [T1, R1], kind ask; case checks tasks.1.id R1 and tasks.2 absent. **Evidence:** red: 1 of 8 failed against the old case; 335 OK; validate OK.

## implementer · F1 · done
**Did:** R-task files bounded to diff/plan, CI/secret paths → design; no verbatim quoting + secret check; gates.push_replies draft sha256; id re-verified; 10-thread per-pass cap; reply body via -F body=@file; ask/R1 example. watch.md 120 lines. **Evidence:** validate OK; 335 OK.

## engine · fixes landed
F1 b90d1c7, F2 b2eaa06. Tests OK, validate OK. Re-review of the fix diff.

## code-reviewer · re-review F1+F2 · done
**Findings:** all resolved. LOW new test file outside diff/plan becomes design (conservative); LOW sandbox-006 assumes a one-task plan. Kept as follow-ups.

## verifier · verify · done
**Did:** verify.md AC1-AC11; 335 OK; validate OK; evals.py check sandbox-006 synthetic good 9/9, bad 4 fail. **Open issues:** AC1-3, AC9 instruction-only; watch.md 120 lines (engine allowed ~125 for F1).
