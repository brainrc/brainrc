# Log: 099-hooks-in-aicfg-home

## engine · intake · done
2026-10-25T23:17:57Z

**Did:** Child 4 of campaign gh:92. Branch 099-hooks-in-aicfg-home from 098-hooks-fail-open. ticket.md from gh:99. Size standard (guards' availability; changes install layout), mode fallback, domains: scripting, offline only.

**Evidence:**
- `python3 -m unittest discover -s tests` → 386 passed (on base b2a5a6d)

**Changed files:** specs/099-hooks-in-aicfg-home/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-25T23:18:27Z

**Did:** Wrote spec.md: 6 criteria (copy when installed, survives package removal, refresh on upgrade, checkout unchanged, migrate old link, disabled harness cleanup), extends aicfg-apply.

**Evidence:**
- `living_specs.py check` → OK

**Changed files:** specs/099-hooks-in-aicfg-home/spec.md

**Open issues:** 1 open question (copy only when installed vs always).

**Next:** Spec gate

## analyst · spec (revision 1) · done
2026-10-25T23:20:37Z

**Did:** Architect found Cursor's guard runs Claude's guards from `<root>/claude/hooks`; per-harness copies would leave Cursor unguarded when Claude is disabled. AC1: copy every core hooks dir. AC6: remove the copy only when no harness with hooks is enabled.

**Evidence:**
- overrides/cursor/hooks/guard.py:17 `HOOKS = Path(__file__).resolve().parent.parent.parent / "claude" / "hooks"`
- `living_specs.py check` → OK

**Changed files:** specs/099-hooks-in-aicfg-home/spec.md

**Open issues:** none

**Next:** Spec gate (again)

## architect · plan · done
2026-10-25T23:23:39Z

**Did:** Wrote plan.md: 3 tasks. `Link.copy` (src overrides, dest $AICFG_HOME/hooks/core) for core hooks when installed; state "update" when the copy is stale; cli copies all core hook dirs via temp dir + rename before linking; prune the copy when no link needs it.

**Evidence:** read-only inspection of plan.py (Link, plan, _managed_target), cli.py apply loop, doctor._link_finding, InstalledModeTest.

**Changed files:** specs/099-hooks-in-aicfg-home/plan.md

**Open issues:** none. Callouts: new $AICFG_HOME/hooks/core; apply may rmtree it.

**Next:** Plan gate
