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
