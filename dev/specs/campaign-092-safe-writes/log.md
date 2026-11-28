# Campaign gh:92 log

## 2026-10-25T18:36:55Z · intake
- Members: gh:96, gh:97, gh:98, gh:99 (sub-issue order). All open, unassigned. None skipped.
- Shape: ordered (`--shape ordered`; members differ, no links).
- Dependencies: API `blocked_by` empty for every child; body fallback finds no `Depends on #N` lines. Source `none`: epic order.
- Order: 96, 97, 98, 99. No cycle, no out-of-epic link.
- Epic body suggests `stacked` delivery and a dry run first; delivery is chosen at the Deliver gate (recorded `sequential` default until then).

## 2026-10-25T18:36:55Z · Campaign gate presented

## 2026-10-25T18:37:58Z · Campaign gate approved
- Child 1 gh:96 started: specs/096-keep-mode-follow-symlinks/ on branch 096-keep-mode-follow-symlinks (from main).

## 2026-10-25T19:40:36Z · child 1 gh:96 verified
- Drafts ready; waits for the stack Deliver gate. Child 2 gh:97 starts on 097-apply-lock-unique-tmp from 096-keep-mode-follow-symlinks.

## 2026-10-25T20:05:58Z · child 2 gh:97 verified
- Drafts ready. Child 3 gh:98 starts on 098-hooks-fail-open from 097-apply-lock-unique-tmp.

## 2026-10-25T23:17:24Z · child 3 gh:98 verified
- Drafts ready. Child 4 gh:99 starts on 099-hooks-in-aicfg-home from 098-hooks-fail-open.
- Finding: a fragment change makes the generated plugin manifests stale, and plans need to fence them (and tests that pin hook commands) in. Candidate architect rule.

## 2026-10-25T23:46:44Z · child 4 gh:99 verified; stack Deliver gate presented
- Finding: a real 3.12→3.13 upgrade shows skill/agent links into the old venv as CONFLICT (pre-existing); follow-up.

## 2026-10-25T23:56:12Z · stack Deliver gate approved (stacked)
- gh:96 → #212 (base main), gh:97 → #213 (base 096), gh:98 → #214 (base 097), gh:99 → #215 (base 098). Comments posted on #96–#99. Merge in order; before each merge, merge main into the branch, re-run tests, retarget to main (`gh pr edit <n> --base main`).

## 2026-10-27T01:09:40Z · landing
- #212 → v0.3.42, #213 → v0.3.43, #214 → v0.3.44 merged in order; before each, main merged into the next branch, tests re-run, PR retargeted to main (REST, local gh is too old for `pr edit --base`). #215 retargeted to main; last to merge.
