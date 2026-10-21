## analyst · spec stage · done
2026-10-21

**Did:** Wrote spec.md for gh:71 with 8 acceptance criteria. It creates a new living area, `run-pointer`, with 3 ADDED requirements. Non-goals exclude the mod itself, a per-session map and pointer cleanup.

**Evidence:**
- `living_specs.py check` (engine) → would update specs/living/run-pointer.md, exit 0

**Changed files:** `specs/071-active-run-pointer/spec.md`

**Open issues:** 4 open questions (write moments, script vs steps, write failure, "abandoned").

**Next:** present the Spec gate.

## analyst · spec 071 record answers · done
2026-10-21

**Did:** Recorded the four gate answers as decisions: write at intake, resume and every checkpoint commit (AC6); writer is `scripts/active_run.py` with `write`/`read` (AC9); read fallback (AC10); warn and exit 0 on write failure (AC11); abandoned needs no action (AC7). Open questions: None.

**Evidence:** 12 criteria; engine `living_specs.py check` exit 0.

**Changed files:** `specs/071-active-run-pointer/spec.md`

**Next:** architect.

## architect · plan stage · done
2026-10-21

**Did:** Plan with 3 tasks: T1 test-writer contract tests; T2 implementer `active_run.py` (after T1); T3 implementer docs + changelog fragment. All `review: each`. `read` with no run anywhere: prints nothing, exit 1.

**Evidence:** read spec, state.md, lifecycle.md, SKILL.md, living_specs.py, test_living_specs.py, aicfg/config.py.

**Changed files:** `specs/071-active-run-pointer/plan.md`

**Open issues:** new external contract (pointer file + CLI) called out.

**Next:** Plan gate.

## test-writer · T1 · done
2026-10-21

**Did:** 17 subprocess contract tests in tests/test_active_run.py (temp AICFG_HOME/HOME/cwd). Applied review: nothing-found read asserts exit 1 + stderr; blank and file pointers fall back to cwd specs; longer first slug in the replace test; type hint fixed.

**Evidence:**
- `python3 -m unittest -q tests.test_active_run` → 17 not passing (14 failed, 3 errors): script absent. red: compile-only (accepted).

**Changed files:** `tests/test_active_run.py`

## code-reviewer · T1 · done
2026-10-21

**Findings:**
- MEDIUM test_active_run.py:144 nothing-found test passed vacuously → assert exit 1 + stderr (fixed)
- MEDIUM no blank/file pointer tests → added (fixed)
- LOW equal-length paths in replace test → fixed
- LOW wrong type hint → fixed

**Next:** T2.

## implementer · T2 · done
2026-10-21

**Did:** Stub first (11 assertion failures + 6 errors against it), then `active_run.py`: `write` via temp file + `os.replace`, creates the home, warns and exits 0 on `OSError`/`RuntimeError`; `read` prefers the pointer, else newest `specs/*/state.json` by mtime (skipping entries whose stat fails), else stderr note + exit 1. Review fixes applied.

**Evidence:**
- `python3 -m unittest -q tests.test_active_run` → 17 OK
- full suite (engine) → 234 OK; `aicfg.py validate` → OK
- red: assertion (against the stub)

**Changed files:** `skills/spec-agent/scripts/active_run.py`

## code-reviewer · T2 · done
2026-10-21

**Findings:**
- MEDIUM active_run.py:34,52 `Path.home()` raises RuntimeError without HOME/passwd → caught in write and read (fixed, untested: tests fenced)
- LOW active_run.py:58 stat() in sort key can raise → skip entries (fixed)
- LOW fd leak if fdopen fails → negligible, not fixed
- LOW relative AICFG_HOME resolves against cwd → matches aicfg_home(), no change

**Next:** T3.

## implementer · T3 · done (attempt 1)
2026-10-21

**Did:** state.md `## Active run pointer` section; write calls in state.md checkpoint rule and Resume, lifecycle.md intake, SKILL.md Run steps 1 and 3; changelog fragment.

**Evidence:** validate OK; full suite 234 OK.

## code-reviewer · T3 · changes-requested
2026-10-21

**Findings:**
- HIGH SKILL.md:75,84, state.md:110,127,131, lifecycle.md:37 `write specs/<slug>` is relative; with cwd reset to the session dir it silently records a nonexistent path → require the absolute run path
- LOW state.md section says absolute but the call passes relative → fixed by the above

## implementer · T3 · done (attempt 2)
2026-10-21

**Did:** All six `active_run.py write` calls pass `<project root>/specs/<slug>`; state.md says the path must be absolute because the shell's directory may not be the repo.

**Evidence:** validate OK; full suite 234 OK.

## code-reviewer · T3 · done (re-review of the fix)
2026-10-21

**Findings:**
- HIGH relative path → resolved
- LOW absolute/relative mismatch → resolved
- LOW (optional) `write()` doesn't check the directory exists → follow-up, script out of T3 scope
