# Campaign gh:94 · Epic E3: Neutral core and doc drift

## 2026-11-10T06:04:53Z · intake
- Started as `/work --campaign gh:94 --shape ordered --oneshot` from the owner's request to work the highest-priority epic in campaign mode and hand back ready PRs for review.
- Why this epic: it is the only open epic whose children are all roadmap wave P0 (P0-9, P0-8, P0-11). E6 (#113, P1) already has its stacked PRs open; D1 (#95) is owner-only.
- Members: gh:104, gh:105, gh:203 (sub-issue order). All open, unassigned. None skipped.
- Shape: ordered (`--shape ordered`; members differ).
- Dependencies: the `blocked_by` API is empty for every child, so the body fallback was used. No `Depends on #N` line. Source `none`: epic order.
- Order: 104, 105, 203. No cycle, no out-of-epic link.
- `--oneshot`: children run as `--oneshot`, `stacked`, every PR ready. Mode inline.

## engine · Campaign gate · auto-approved
2026-11-10T06:04:53Z
⛔ Campaign gate: campaign-094-neutral-core
Summary: ordered shape, 3 children in epic order (source none). Child N branches from child N-1; each gets its own Spec and Plan gates (auto-approved under `--oneshot`).
Decide: shape and order.
Artifacts: specs/campaign-094-neutral-core/campaign.json

- Child 1 gh:104 started: specs/104-local-tripwires/ on branch 104-local-tripwires (base main).

## 2026-11-10T06:11:42Z · child 1 gh:104 verified
- Drafts ready (specs/104-local-tripwires/pr-body.md). Child 2 gh:105 branches from 104-local-tripwires.

## 2026-11-10T06:18:49Z · child 2 gh:105 verified
- One retry (old-name test). Drafts ready (specs/105-fix-doc-drift/pr-body.md). Child 3 gh:203 branches from 105-fix-doc-drift.

## 2026-11-10T06:21:03Z · child 3 gh:203 verified

## engine · stack Deliver gate · auto-approved
2026-11-10T06:21:03Z
⛔ Deliver gate: campaign-094-neutral-core (stacked, oneshot)
Outward actions, in merge order:
1. Push 104-local-tripwires; open a ready PR against main from specs/104-local-tripwires/pr-body.md.
2. Push 105-fix-doc-drift; open a ready PR against 104-local-tripwires from specs/105-fix-doc-drift/pr-body.md ("2 of 3, stacked on #X").
3. Push 203-roadmap-epic-list; open a ready PR against 105-fix-doc-drift from specs/203-roadmap-epic-list/pr-body.md ("3 of 3, stacked on #X").
Ticket comments stay drafts. No ticket transition, no merge, no retarget.
