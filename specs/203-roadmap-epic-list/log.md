# Log: 203-roadmap-epic-list

## engine · intake
gh:203 via ticket-github, child 3 of 3 in campaign gh:94 (`campaign-094-neutral-core`), branched from 105-fix-doc-drift. `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size small (one doc rewrite plus a shape test), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/203-roadmap-epic-list`.

## engine · Spec gate · auto-approved
4 criteria (AC1–AC4). Defaults: wave = Roadmap ID prefix; E17 and E18 listed; fresh goal lines; README unchanged. `living_specs.py check`: no requirement changes. Plan stage skipped (small).

## code-reviewer · gh:203 batch · done
Inline (review_context: shared). No CRITICAL/HIGH/MEDIUM. 1 LOW: the page is a hand-kept snapshot and will drift; stated in its header.

## engine · verify
724 tests OK, validate OK. Live diff: 25 open epics, 25 listed.

## engine · Deliver gate · auto-approved
2026-11-10T06:21:03Z
Push 203-roadmap-epic-list, open a ready PR from pr-body.md against 105-fix-doc-drift (stacked, Closes #203). Ticket comment stays a draft. No ticket transition.

## engine · watch · review on #265
Inline finding (bxker): the wave test only checked that a `## Wave 0` heading came first. Now every item must sit under one of the six wave or group headings (fails with an item under `## Notes`). Also reworded `docs/formats.md`'s "Adapters (see roadmap)", which the new page no longer covers.
