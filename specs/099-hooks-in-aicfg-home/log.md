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

## implementer · T1 · done
2026-10-25T23:27:27Z

**Did:** `config.hooks_copy_root()`; `Link.copy` + `hooks_copy_current` in plan.py (state "update" when the copy differs); installed core hooks link to $AICFG_HOME/hooks/core/<h>/hooks; cli `_copy_hooks` builds all core hook dirs in a temp sibling and swaps it in before linking.

**Evidence:**
- red: 4 InstalledModeTest tests fail on behavior (link target is the package; no copy; no UPDATE); checkout test passes before (regression guard)
- `python3 -m unittest discover -s tests` → 391 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** aicfg/config.py, aicfg/plan.py, aicfg/cli.py, tests/test_aicfg.py

**Open issues:** none

**Next:** review T1

## code-reviewer · T1 · done
2026-10-25T23:27:27Z

**Did:** Reviewed T1 diff against AC1–AC5.

**Findings:**
- LOW aicfg/doctor.py (via Link.state): a stale copy shows as "points at the wrong item"; the fix (`apply`) is right, the wording is generic.
- LOW aicfg/plan.py:_hook_files: `__pycache__` is matched against the absolute path parts → only matters if $AICFG_HOME's own path contains `__pycache__`.

**Open issues:** none

**Next:** commit T1

## security-reviewer · T1 · done
2026-10-25T23:27:27Z

**Did:** Checked filesystem writes and removals (security-checklist: Paths).

**Findings:**
- LOW aicfg/cli.py:_copy_hooks: between the two renames the copy is briefly absent, so guards fail open for that instant → accepted in plan Risks.
- none higher: rmtree targets are fixed, pid-named siblings of $AICFG_HOME/hooks/core; copies keep the package's modes.

**Open issues:** none

**Next:** commit T1

## implementer · T2 · done
2026-10-25T23:28:56Z

**Did:** `_managed_target` accepts links into $AICFG_HOME/hooks/core/<h>/hooks (so a disabled harness's link is pruned); `stale_hooks_copy` returns the copy when no link uses it; cli prints PRUNE and removes it on apply.

**Evidence:**
- red: test fails on assertion (cursor link into the copy not pruned)
- `python3 -m unittest discover -s tests` → 392 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** aicfg/plan.py, aicfg/cli.py, tests/test_aicfg.py

**Open issues:** none

**Next:** review T2

## code-reviewer · T2 · done
2026-10-25T23:28:56Z

**Did:** Reviewed T2 diff against AC6.

**Findings:**
- LOW aicfg/plan.py:stale_hooks_copy: a checkout that once ran installed also prunes the leftover copy → desirable; untested.

**Open issues:** none

**Next:** commit T2

## security-reviewer · T2 · done
2026-10-25T23:28:56Z

**Did:** Checked the new `rmtree` (security-checklist: Paths).

**Findings:** none. The path is fixed (`$AICFG_HOME/hooks/core`), removed only when no link uses it, and it holds only aicfg's copy.

**Open issues:** none

**Next:** commit T2

## implementer · T3 · done
2026-10-25T23:29:10Z

**Did:** docs/install.md: installed guard hooks are copied to $AICFG_HOME/hooks/core; run `aicfg apply` after upgrading.

**Evidence:**
- `python3 scripts/aicfg.py validate` → OK (docs-only)

**Changed files:** docs/install.md

**Open issues:** none

**Next:** batched review (T3)
