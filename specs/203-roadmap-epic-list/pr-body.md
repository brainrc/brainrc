List the open epics by wave in docs/roadmap.md

Part of epic #94 (E3), 3 of 3, stacked on #PR105. Retarget to `main` before merging. Closes #203.

## Why
`docs/roadmap.md` still listed three old items. The plan lives in the GitHub epics now, so someone reading the repo couldn't see what comes next.

## What changed
- `docs/roadmap.md` lists all 25 open epics, one line each: ID, title linked to its issue, and a one-line goal. They're grouped by wave, which is the `Roadmap ID` prefix of the epic's sub-issues (P0 to P4), with three more groups: owner decisions (D1), epics added after the waves (E17, E18, E23–E25), and open epics whose sub-issues are all closed (E2, E22).
- The page says shipped work is in the CHANGELOG, and that an epic's own "Start after" note wins over the page order.
- New `tests/test_roadmap.py` keeps every item a linked epic, with no repeated ID or issue, under a wave heading.

## Acceptance criteria
- [x] AC1: every open epic is listed once. Verified by diffing the open epics from the GitHub API (titles starting "Epic", plus #63 and #18) against the page's issue links: 25 and 25.
- [x] AC2: grouped by wave, with owner, unwaved and finished groups.
- [x] AC3: links the CHANGELOG.
- [x] AC4: `RoadmapTest` checks the line shape (it fails on the old page).

## How to verify
```
python3 -m unittest tests.test_roadmap
python3 scripts/brainrc.py validate
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Campaign, Spec, Deliver. See `specs/203-roadmap-epic-list/log.md`.
- "Wave" is read as the `Roadmap ID` prefix (P0–P4) of the sub-issues. Nothing else in the repo or issues defines waves.
- E17 (#63) and E18 (#18) are listed though they aren't titled "Epic", because their sub-issues carry those IDs.
- The goal lines are new wording; the epic bodies hold run instructions, not goals. No sub-issue counts, since those go stale.
- README is unchanged: it already links the roadmap, and the E6 stack (#259) is rewriting it.

## Follow-ups
- **You:** E2 (#93) and E22 (#199) have every sub-issue closed and can be closed.
- The page is hand-kept. Generating it from the API would need network in CI, so it stays a follow-up idea.

Spec: `specs/203-roadmap-epic-list/spec.md` · Plan: `specs/203-roadmap-epic-list/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
