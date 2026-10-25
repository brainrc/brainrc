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
