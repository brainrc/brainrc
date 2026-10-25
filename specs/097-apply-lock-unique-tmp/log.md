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
