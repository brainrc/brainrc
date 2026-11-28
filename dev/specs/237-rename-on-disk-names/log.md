# Log: 237-rename-on-disk-names

## engine · intake, spec, plan · done
2026-10-29T02:16:01Z
Owner: stop only at Deliver. Spec (engine-written, living check passes) and a one-task plan auto-approved; defaults for 2 questions listed at Deliver. Callouts: none (on-disk names converge; no user-facing contract change).

## implementer · T1 · partial, then engine completion
2026-10-29T02:40:00Z
The implementer implemented AC1-AC3 and the fallback and write sides of AC4. It needed one call in `brainrc/cli.py`, outside the file list, so it handed back. The engine added `brainrc/cli.py` to T1's files. The `_sync` change calls `adopt_record` for each git pack on apply. The test was changed to go through apply, not call `adopt_record` directly; it was red first, then green. Suite: 590 OK, with and without XDG; validate OK.

## code-reviewer · T1 · changes-requested, then fixed
2026-10-29T03:00:00Z
1 blocking finding: user blank lines were lost around a mid-file old block. The block is now replaced in place, with an exact-bytes test that was red first. 4 should-fix findings, all fixed: a corrupt new record is repaired; a stale old record is removed; a failed record write on a read-only `.git` is ignored; there is a test for an unterminated block. 1 test nit fixed.

## engine · verify, document · done
2026-10-29T03:05:00Z
Suite OK with and without XDG; validate OK. verify.md and pr-body.md written. Living spec applied. Deliver gate pending.

## owner · deliver gate · approved
2026-10-29T04:20:00Z
The owner approved: push, then a ready PR.

## engine · deliver · done
2026-10-29T04:30:00Z
Pushed; ready PR #237 opened.

## engine · watch · done
2026-10-29T04:50:00Z
#237 merged; release v0.4.7 (c43c0bd). Post-merge verify passed on main (verify-merged.md).
