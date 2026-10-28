# Campaign gh:199 · Epic E22: Rename to brainrc

## 2026-10-27T18:43:34Z · intake
- Members: gh:204, gh:205, gh:206, gh:207, gh:208, gh:209 (sub-issue order). All open, unassigned. None skipped.
- Shape: ordered (`--shape ordered`; members differ).
- Dependencies: MCP only, so the body fallback: no `Depends on #N` lines in any child. Source `none`: epic order.
- Order: 204, 205, 206, 207, 208, 209. No cycle, no out-of-epic link.
- Epic's ordering note "start after #201" (repo move): `origin` already resolves to github.com/brainrc/brainrc, so the move is done; #201 itself is still open (owner action).
- `--auto`: `auto: true`. Stack Deliver gate will be `stacked` draft PRs, and only if no child is blocked.

## engine · Campaign gate · auto-approved
2026-10-27T18:45:03Z
⛔ Campaign gate: campaign-199-rename-brainrc
Summary: ordered shape, 6 children in epic order (source none). Each child gets its own Spec and Plan gates (auto-approved), and child N branches from child N-1.
Decide: shape and order.
Artifacts: specs/campaign-199-rename-brainrc/campaign.json

- Child 1 gh:204 started: specs/204-point-urls-brainrc/ on branch 204-point-urls-brainrc (from main).

## 2026-10-27T18:47:20Z · child 1 gh:204 verified
- Size small, inline. Drafts ready; waits for the stack Deliver gate. Child 2 gh:205 starts on its branch from 204-point-urls-brainrc.

## 2026-10-27T18:48:46Z · child 2 gh:205 blocked (auto hard stop: size large)
- Spec written with a 3-child Proposed split; needs approval. Children 3-6 paused. Stack has a blocked child, so no PRs open (gh:204 stays verified, unpushed).

## 2026-10-28T01:16:33Z · gh:204 delivered on its own
- Owner: "ship 204". Draft PR #229, base main. Campaign stays paused on gh:205 (blocked, size large). When #205 is unblocked, its branch merges main (after #229 merges) instead of building on 204-point-urls-brainrc.

## 2026-10-28T01:39:38Z · gh:204 merged (#229); gh:205 resumed
- #229 merged 01:30Z (v0.3.50). Owner: "resize standard" for gh:205; campaign continues without --auto (gates stop). 205 branch now based on main.

## 2026-10-28T02:47:03Z · gh:205 delivered
- Draft PR #230, base main (sequential: #229 already merged). Next: gh:206 after #230 merges.

## 2026-10-28T03:15:07Z · gh:205 merged (#230), v0.4.0 released
- Post-merge verify pass. Child 3 gh:206 starts on 206-brainrc-settings-home from main.
