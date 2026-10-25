# Log: 097-apply-lock-unique-tmp

## engine · intake · done
2026-10-25T19:40:58Z

**Did:** Child 2 of campaign gh:92. Branch 097-apply-lock-unique-tmp from 096-keep-mode-follow-symlinks. ticket.md from gh:97. Size standard (concurrency, writes secrets file), mode fallback, domains: scripting, offline only.

**Evidence:**
- `python3 -m unittest discover -s tests` → 373 passed (on base 3204da0)

**Changed files:** specs/097-apply-lock-unique-tmp/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-25T19:41:26Z

**Did:** Wrote spec.md: 6 criteria (lock, release, pid temp names, changed-during-apply guard, status unlocked, docs), extends living area aicfg-apply.

**Evidence:**
- `living_specs.py check` → OK

**Changed files:** specs/097-apply-lock-unique-tmp/spec.md

**Open issues:** 2 open questions (fail fast vs wait; skip vs re-merge).

**Next:** Spec gate

## architect · plan · done
2026-10-25T19:42:49Z

**Did:** Wrote plan.md: 3 tasks. cli reads `before` and passes it to `replace_file`, which raises `FileChanged` on mismatch; pid temp names; non-blocking flock on $AICFG_HOME/apply.lock around `_sync(True)`; docs.

**Evidence:** read-only inspection of aicfg/cli.py, settings.py, mcp.py, doctor.py call sites.

**Changed files:** specs/097-apply-lock-unique-tmp/plan.md

**Open issues:** none. Callouts: internal signature change (`before` arg), new $AICFG_HOME/apply.lock.

**Next:** Plan gate

## implementer · T1 · done
2026-10-25T19:44:37Z

**Did:** `read_current` + `FileChanged` in settings.py; `replace_file` re-reads the target and raises before writing when it no longer holds `before`; temp name `.<name>.aicfg-tmp-<pid>`. cli reads `before` per file, prints CHANGED with the close-Claude-Code hint, exits 1; `record_owned` skipped for a changed MCP file.

**Evidence:**
- red: 3 new tests fail on assertions (temp name lacks pid; exit 0 != 1 ×2)
- `python3 -m unittest discover -s tests` → 376 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** aicfg/settings.py, aicfg/mcp.py, aicfg/cli.py, tests/test_aicfg.py, tests/test_mcp.py

**Open issues:** none

**Next:** review T1

## code-reviewer · T1 · done
2026-10-25T19:44:37Z

**Did:** Reviewed T1 diff against AC3, AC4. Not a security trigger beyond gh:96's (no new paths or modes), so no security review.

**Findings:**
- LOW aicfg/settings.py:replace_file: the check runs before the backup and temp write, so a write landing in those few ms is still lost → spec non-goal (final window); docs say to close Claude Code.
- LOW aicfg/cli.py:CHANGED_HINT: names Claude Code also for Codex/OpenCode files → acceptable; Claude Code is the harness known to rewrite its config while running.

**Open issues:** none

**Next:** commit T1

## implementer · T2 · done
2026-10-25T19:45:59Z

**Did:** `cmd_sync(True)` takes a non-blocking flock (msvcrt on Windows) on $AICFG_HOME/apply.lock via `_try_lock`, runs `_sync(True)` inside it; held lock → ERROR naming the lock, exit 1, nothing written. `cmd_sync(False)` runs `_sync` unlocked.

**Evidence:**
- red: lock test fails on assertion (exit 0 != 1); release test passes before the change (regression guard)
- `python3 -m unittest discover -s tests` → 378 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** aicfg/cli.py, tests/test_aicfg.py

**Open issues:** none

**Next:** T3

## implementer · T3 · done
2026-10-25T19:46:09Z

**Did:** Added "Apply while something else writes" to docs/troubleshooting.md: close Claude Code before MCP changes; table for the lock and CHANGED messages.

**Evidence:**
- `python3 scripts/aicfg.py validate` → OK (docs-only task, no test)

**Changed files:** docs/troubleshooting.md

**Open issues:** none

**Next:** batched review (T2, T3)

## code-reviewer · batch (T2, T3) · done
2026-10-25T20:05:39Z

**Did:** Reviewed T2 and T3 diffs against AC1, AC2, AC5, AC6. review_context: shared (user chose to continue here).

**Findings:**
- LOW aicfg/cli.py:cmd_update: pack fetches run before the lock → spec non-goal.

**Open issues:** none

**Next:** verify

## verifier · verify · done
2026-10-25T20:05:39Z

**Did:** Suite and validate once, 6 targeted tests, real two-process lock check on a scratch copy. 6/6 criteria pass.

**Evidence:**
- `python3 -m unittest discover -s tests` → 378 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** specs/097-apply-lock-unique-tmp/verify.md

**Open issues:** none

**Next:** document

## doc-writer · document · done
2026-10-25T20:05:58Z

**Did:** Applied the living-spec delta (2 requirements added to aicfg-apply), added changelog.d/097-apply-lock-unique-tmp.md (patch), drafted pr-body.md and ticket-comment.md. Docs were done in T3.

**Evidence:**
- `living_specs.py apply` → updated specs/living/aicfg-apply.md
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** specs/living/aicfg-apply.md, changelog.d/097-apply-lock-unique-tmp.md, specs/097-apply-lock-unique-tmp/pr-body.md, specs/097-apply-lock-unique-tmp/ticket-comment.md

**Open issues:** none

**Next:** child verified; campaign continues with child 3

## engine · deliver · done
2026-10-25T23:56:12Z

**Did:** Stacked delivery approved at the campaign Deliver gate. PR null opened (draft), ticket comment posted, retro.md written; stage watch.

**Next:** watch (pull-based, on /spec-resume)
