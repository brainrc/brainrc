# Log: 098-hooks-fail-open

## engine · intake · done
2026-10-25T20:06:53Z

**Did:** Child 3 of campaign gh:92. Branch 098-hooks-fail-open from 097-apply-lock-unique-tmp. ticket.md from gh:98. Size standard (security trigger: guard hooks fail open), mode fallback, domains: scripting, offline only.

**Evidence:**
- `python3 -m unittest discover -s tests` → 378 passed (on base 82bb448)

**Changed files:** specs/098-hooks-fail-open/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-25T20:07:15Z

**Did:** Wrote spec.md: 7 criteria (Claude and Cursor fail open, unchanged guard behavior, doctor missing/broken/healthy, upgrade replaces old groups), extends aicfg-apply.

**Evidence:**
- `living_specs.py check` → OK

**Changed files:** specs/098-hooks-fail-open/spec.md

**Open issues:** 1 open question (Cursor: explicit allow vs empty output).

**Next:** Spec gate

## architect · plan · done
2026-10-25T20:09:16Z

**Did:** Wrote plan.md: 3 tasks. Fail-open sh wrappers in the two fragments (no code change; OWNED_HOOK still matches, AC7). Doctor `_hook_findings` extracts each owned hook's script path, reports missing, runs present ones with `{}` and the hook timeout.

**Evidence:** read-only inspection of fragments, plan.py render_fragment, config.hook_command_dir, doctor.py, test_hooks.py.

**Changed files:** specs/098-hooks-fail-open/plan.md

**Open issues:** none. Callouts: hook command form changes in users' settings; doctor runs local scripts (arg list, no shell).

**Next:** Plan gate
