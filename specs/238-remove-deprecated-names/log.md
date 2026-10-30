# Log: 238-remove-deprecated-names

## engine · intake, spec, plan · done
2026-10-29T03:15:00Z
Owner: stop only at Deliver. Stacked on 237, since both touch the old-name allowlist. The engine wrote the spec; the living check passes. The plan is one task. Both gates were auto-approved. Defaults for 3 questions will be listed at Deliver. Callouts: a **[pack contract]** minor bump; an unmigrated old home now stops status, apply and update.

## implementer · T1 · done
2026-10-29T03:45:00Z
Removed the deprecated names and added the refusal for an unmigrated home. The implementer found that 236's check was not on this branch, so the engine merged branch 236 in and adapted its test to patch `SHIM_REMOVED_IN` in.

## code-reviewer · T1 · approved with should-fix findings
2026-10-29T04:00:00Z
No blocking findings. Fixed: the install note wording, the living specs (applied) and a vacuous doctor assertion. Two nits were left as is; they are listed in verify.md.

## engine · verify, document · done
2026-10-29T04:10:00Z
Suite OK with and without XDG; validate OK, including the example pack. Wheel install check OK. Deliver gate pending.

## owner · deliver gate · approved
2026-10-29T04:20:00Z
The owner approved: push, then a ready PR.

## engine · deliver · done
2026-10-29T04:30:00Z
Pushed; ready PR #239 opened.

## engine · watch · done
2026-10-29T04:50:00Z
#239 merged; release v0.5.0 (7e758d4). Post-merge verify passed on main (verify-merged.md).
