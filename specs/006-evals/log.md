## analyst · spec · done
2026-10-06T02:43:57Z

**Did:** Wrote spec.md from gh:6: offline run checker with two sandbox cases, trigger runner (prompt or any model CLI), pack-extensible, offline tests in CI, docs, 0.3.5.

**Evidence:**
- intake: no open PRs; size standard; mode fallback; only Claude Code installed here (no codex/opencode/gemini/cursor); claude CLI present, no headless credentials visible

**Changed files:** `specs/006-evals/spec.md`

**Open issues:** 7 criteria, 3 open questions with defaults

**Next:** Spec gate

## architect · plan · done
2026-10-06T02:50:45Z

**Did:** Wrote plan.md: one stdlib script (check, triggers), 7 check kinds, batch trigger prompt with JSON answer, offline tests with a fake model; 4 tasks.

**Evidence:**
- read sandbox tickets, verify.md table format, aicfg sources()

**Changed files:** `specs/006-evals/plan.md`

**Open issues:** callouts: subprocess use (no shell); AC3 .env check reworded to "no .env file created or committed"

**Next:** Plan gate

## test-writer · T1 · done
2026-10-06T02:52:32Z

**Did:** tests/test_evals.py: all 9 checks pass on a good fake run; each kind fails on its broken variant (state, verify row, missing/forbidden pattern, command exit/stdout, commit on main, missing branch, committed .env); unknown ticket; trigger scoring, prompt contents, chatty-JSON extraction, --cmd with a fake model, print mode; coverage of every Domains skill and known kinds in case files.

**Evidence:**
- `python3 -m unittest tests.test_evals` → FileNotFoundError scripts/evals.py (compile-only red)

**Changed files:** `tests/test_evals.py`

**Open issues:** red is compile-only

**Next:** review T1

## code-reviewer · T1 · done
2026-10-06T02:52:32Z

**Did:** Reviewed T1 against AC1, AC4, AC6.

**Evidence:**
- each kind has a pass and a fail path; fixtures are throwaway git repos

**Changed files:** none

**Findings:** none

**Open issues:** none

**Next:** commit T1, then T2 (stub first)

## implementer · T2 · done
2026-10-06T02:53:57Z

**Did:** scripts/evals.py check: run lookup by ticket_ref, 7 check kinds, PASS/FAIL lines and summary, ERROR on setup problems. Cases sandbox-001 (11 checks) and sandbox-002 (10 checks). Test fix: commit-on-main test now grades from the run's branch, as after a real run.

**Evidence:**
- stub red: 15 assertion failures; CheckTest 10/10 OK; case files use known kinds; no-run sandbox → clean ERROR, exit 1

**Changed files:** `scripts/evals.py`, `evals/cases/sandbox-001.toml`, `evals/cases/sandbox-002.toml`, `tests/test_evals.py`

**Open issues:** none

**Next:** review T2

## code-reviewer · T2 · done
2026-10-06T02:53:57Z

**Did:** Reviewed T2 against AC1, AC2, AC3, AC5.

**Evidence:**
- subprocess calls use argument lists, no shell; missing check fields surface as ERROR

**Changed files:** none

**Findings:**
- LOW scripts/evals.py verify: missing verify.md raised instead of FAIL → fixed in the same attempt.

**Open issues:** none

**Next:** commit T2, then T3
