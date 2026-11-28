# Campaign gh:109 · Epic E4: First-run CLI

## 2026-11-10T16:29:57Z · intake
- Started as `/work --campaign gh:109 --shape ordered --oneshot` from the owner's request to pick the next highest-impact epic and complete it in campaign mode.
- Why this epic: E3 (wave 0) shipped, so wave 1 is next. Of E4, E5 and E6, E4 is the one the others wait on: E6's own "Start after" names E4, and E5's playbook edits the same harness paths E4 starts to detect. E6 already has open stacked PRs (#257 to #262); D1 (#95) is owner-only.
- Members: gh:125, gh:126, gh:127, gh:128, gh:129, gh:130 (sub-issue order). All open, unassigned. None skipped.
- Shape: ordered (`--shape ordered`, as the epic says; members differ).
- Dependencies: the `blocked_by` API is empty for every child and no body has a `Depends on #N` line. Source `none`: epic order.
- Order: 125, 126, 127, 128, 129, 130. No cycle, no out-of-epic link.
- `--oneshot`: children run as `--oneshot`, `stacked`, every PR ready. Mode inline.
- Names: the tickets predate the rename, so `aicfg` in them reads as `brainrc` and `aicfg/` as `brainrc/`.

## engine · Campaign gate · auto-approved
2026-11-10T16:29:57Z
⛔ Campaign gate: campaign-109-first-run-cli
Summary: ordered shape, 6 children in epic order (source none). Child N branches from child N-1; each gets its own Spec and Plan gates (auto-approved under `--oneshot`).
Decide: shape and order.
Artifacts: specs/campaign-109-first-run-cli/campaign.json

- Child 1 gh:125 started: specs/125-argparse-cli/ on branch 125-argparse-cli (base main).

## 2026-11-10T16:38:00Z · child 1 gh:125 verified
- Drafts ready (specs/125-argparse-cli/pr-body.md). Child 2 gh:126 branches from 125-argparse-cli.

## 2026-11-10T16:54:00Z · child 2 gh:126 verified
- Drafts ready (specs/126-installed-harnesses/pr-body.md). Child 3 gh:127 branches from 126-installed-harnesses.

## engine · child 3 · verified
gh:127 `127-brainrc-init` verified at 2026-11-10T17:03Z: 779 tests, validate OK. Content profiles left to #173 (owns profiles).

## engine · child 4 · verified
gh:128 `128-brainrc-uninstall` verified at 2026-11-10T17:20Z: 790 tests, validate OK.

## engine · child 5 · verified
gh:129 `129-apply-repair` verified at 2026-11-10T17:32Z: 799 tests, validate OK.

## engine · child 6 · verified
gh:130 `130-doctor-plugin-overlap` verified at 2026-11-10T17:37Z: 805 tests, validate OK. Every child verified.

## engine · stack Deliver gate · auto-approved
`delivery: stacked`. Ready PRs opened 2026-11-10T17:39Z: #267 (125) on main, then #268 (126), #269 (127), #270 (128), #271 (129), #272 (130), each on the previous child's branch with "N of 6, stacked on #X. Retarget to `main` before merging." Ticket comments stay drafts; no ticket transitions. Merge order is 267 → 272; after each merge, merge `main` into the next branch, re-run its tests, and retarget its PR to `main` (Retarget rule). Never merged by the run.

## code-reviewer · E4 review · fixes pushed
#267, #268, #269 and #272 ready to merge with no blocking findings. #270 (purge safety, a crash on an empty user folder, manifest checks) and #271 (repair pruning the user's live links) fixed with tests, merged up the stack into 129 and 130.
