## analyst · spec stage · done
2026-10-21

**Did:** spec.md with 13 criteria, non-goals, new living area `metrics-report` (4 ADDED).

**Evidence:**
- `living_specs.py check` (engine) → would update specs/living/metrics-report.md, exit 0

**Changed files:** `specs/076-metrics-rollup/spec.md`

**Open issues:** 5 questions: criteria-passed source, invalid timestamps (012), ccusage attribution, in-progress duration, aggregate denominators.

## engine · intake · moved
2026-10-21

**Did:** gh:76 was a duplicate of gh:24 (closed as duplicate). Run moved to gh:24: branch and folder renamed to 024-metrics-rollup, ticket.md refetched with #76 criteria folded in as a comment.

## analyst · spec revise for gh:24 · done
2026-10-21

**Did:** Added domain grouping, blocked-stop reporting, Markdown table default, tokens via --ccusage only (no new state.json fields), docs in docs/efficiency.md. 16 criteria, 7 open questions.

**Evidence:** engine `living_specs.py check` exit 0.

**Changed files:** `specs/024-metrics-rollup/spec.md`

## analyst · record gate answers · done
2026-10-21

**Did:** Recorded 7 answers as decisions; added AC17 (criteria-passed source), AC18 (invalid timestamps), AC19 (denominators). Open questions: None. Status approved.

**Evidence:** 19 criteria; engine living_specs check exit 0.

**Changed files:** `specs/024-metrics-rollup/spec.md`

## architect · plan · done
2026-10-21

**Did:** 6 tasks across four stdlib modules (retro_metrics, retro_aggregate, retro_ccusage, retro_report); waves T1+T4, then T2+T3, then T5, then T6 (docs, review batch).

**Changed files:** `specs/024-metrics-rollup/plan.md`

**Open issues:** public contract: CLI + JSON schema_version 1.

## implementer · T1 · done
2026-10-21

**Did:** `load_run` → RunRecord/Skipped; durations, per-stage, rework, first-pass, retries, interventions, waves; unknown = None; bad timestamps flagged, not clamped; durations only for done runs.

**Evidence:** red 18/22 assertion failures vs stub; `tests.test_retro_metrics` 22 OK; full suite 256 OK (worktree).

**Changed files:** `scripts/retro_metrics.py`, `tests/test_retro_metrics.py`

## implementer · T4 · done
2026-10-21

**Did:** `period_totals(since, until)` via `ccusage daily --json --since --until` (argv, timeout, no shell); any failure → available: False with a note.

**Evidence:** red 7 errors (KeyError) vs stub; `tests.test_retro_ccusage` 7 OK; full suite 241 OK (worktree).

**Changed files:** `scripts/retro_ccusage.py`, `tests/test_retro_ccusage.py`

**Open issues:** ccusage flag names and JSON shape assumed (ccusage not installed here).

## engine · wave 1 · landed
2026-10-21

T1 and T4 landed in plan order; worktrees removed. metrics.waves: width 2, 3.6 task-min in 2.2 wall-min.

## implementer · T2 · done
2026-10-21

**Did:** criteria_passed ("n/m") from verify.md Result column by header, retro row fallback; blocked_stops list = current reason + log.md headers with status blocked. Adjusted T1's identity test: blocked_stops is now [] not None.

**Evidence:** red 9 assertion failures; `tests.test_retro_metrics` 32 OK; full suite 273 OK (worktree).

**Changed files:** `scripts/retro_metrics.py`, `tests/test_retro_metrics.py`

## implementer · T3 · done
2026-10-21

**Did:** `aggregate(records)` by size, mode, domain (multi counts under each; none group), final stage; {avg, n} over known values; durations over done runs only; blocked-stop counts and reasons.

**Evidence:** red 12/13 vs stub (4 failures, 8 KeyError errors); `tests.test_retro_aggregate` 13 OK; full suite 276 OK; validate OK (worktree).

**Changed files:** `scripts/retro_aggregate.py`, `tests/test_retro_aggregate.py`

## engine · wave 2 · landed
2026-10-21

T2 and T3 landed in order; integration check aggregates all 36 real runs. metrics.waves now: 2 waves, width 2, 6.3 task-min in 3.7 wall-min.

## implementer · T5 · done
2026-10-21

**Did:** CLI with --root (repeatable, deduped), Markdown default, --json (schema_version, runs, skipped, aggregates, period usage), --ccusage wiring; stub test proves ccusage is never invoked without the flag.

**Evidence:** red: stub gave empty output; `tests.test_retro_report` 11 OK; full suite 297 OK; validate OK; smoke `--root specs` exit 0, no home paths.

**Changed files:** `scripts/retro_report.py`, `tests/test_retro_report.py`

**Open issues:** retro_aggregate.blocked_reasons adds blocked_reason and blocked_stops, which already holds the current block → double count (AC9); T5 test only checks the key exists.

## engine · F1 added
2026-10-21

Two defects from integration: (1) blocked-stop double count (T2/T3 parallel contract mismatch); (2) smoke shows negative agent time for 010 and 026 (gate wait > total from out-of-order timestamps), which AC18 says must be excluded.

## implementer · F1 · done
2026-10-21

**Did:** blocked_reasons reads only blocked_stops (current + 1 past = 2); negative agent and per-stage minutes become unknown with a warning. Updated the aggregate fixture that listed the current block separately.

**Evidence:** red on assertions (3 != 2; -30.0 / -10.0 not None); full suite 300 OK; validate OK; smoke has no negative minutes.

**Changed files:** retro_aggregate.py, retro_metrics.py, test_retro_aggregate.py, test_retro_metrics.py, test_retro_report.py
