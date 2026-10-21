# 078-pr-status-connector log

Campaign gh:77 child 1 of 4. Intake 2026-10-21T04:52:53Z: size standard, mode subagent, domains scripting, offline only, delivery normal. Baseline: 314 tests OK, validate OK.

## analyst · spec · done
**Did:** spec.md, 9 ACs, 4 open questions; delta ADDED in ticket-connectors and evals. **Evidence:** engine ran living_specs.py check: exit 0. **Changed files:** spec.md **Open issues:** thread resolved state; head sha/updated_at; fixture layout; closed state. **Next:** Spec gate.

## engine · spec gate · approved 2026-10-21T04:55:53Z
User approved with the recommended answers to Q1-Q4; engine folded them into AC1, AC3, AC7 and the Open questions section.

## architect · plan · done
**Did:** plan.md, 4 tasks, all wave 1 (disjoint files); shape fixed in plan. **Evidence:** state.json parses. **Changed files:** plan.md, state.json **Open issues:** contract callout (additive). **Next:** Plan gate.

## engine · plan gate · approved 2026-10-21T05:00:58Z
Wave 1 start: T1-T4 in worktrees.

## implementer · T3 · done
**Did:** two ConnectorCheckTest tests (pr_status optional; doesn't replace link_pr). **Evidence:** 316 OK; bite check: adding pr_status to REQUIRED_CONNECTOR_OPS (aicfg/config.py) fails the test, reverted. **Changed files:** tests/test_aicfg.py **Next:** review.

## implementer · T1 · done
**Did:** pr_status row, shape, untrusted rule, skip rule in connectors.md; changelog fragment. **Evidence:** validate OK; 314 tests OK (docs only). **Changed files:** connectors.md, changelog.d/078-pr-status-connector.md **Next:** review (each).

## implementer · T2 · done
**Did:** ticket-github pr_status row + section (GraphQL query, MCP get/get_check_runs/get_review_comments, mapping); post-deliver.md aligned. **Evidence:** validate OK; 314 OK (docs only). **Changed files:** skills/ticket-github/SKILL.md, docs/post-deliver.md **Open issues:** mapped STALE→cancelled, STARTUP_FAILURE→failure (own choice). **Next:** review (each).

## code-reviewer · T1+T2 · changes-requested
**Findings:** HIGH T2 single GraphQL query deviates from approved AC3 (gh pr view for checks/sha/state + GraphQL for threads); MEDIUM first:100 unpaginated; LOW -F owner coerces numerics; LOW MCP row has no mapping. T1 clean. **Next:** engine keeps the approved spec; T2 attempt 2 with findings.

## implementer · T4 · done
**Did:** PrStatusFixtureTest (6 tests); three fixtures under examples/sandbox/pr_status/; README line. **Evidence:** red: 7 assertion failures (fixtures missing); green: 319 OK; validate OK. **Changed files:** tests/test_evals.py, examples/sandbox/README.md, examples/sandbox/pr_status/{red-ci,review-comment,merged}.json **Next:** batch review.

## implementer · T2 attempt 2 · done
**Did:** gh pr view for checks/sha/state/updated_at + GraphQL reviewThreads only; totalCount cap note; -f owner/repo; MCP mapping. **Evidence:** validate OK; 314 OK. **Changed files:** skills/ticket-github/SKILL.md, docs/post-deliver.md **Next:** fix diff joins the batched review with T3, T4.
