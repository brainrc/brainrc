# Log: 129-apply-repair

## engine · intake
gh:129 via ticket-github, child 5 of 6 in campaign gh:109 (`campaign-109-first-run-cli`). `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size standard (link adoption rule, a behavior visible on every moved install), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/129-apply-repair`, base `128-brainrc-uninstall`. Baseline: 790 tests OK, validate OK.

## engine · Spec gate · auto-approved
6 criteria (AC1–AC6). Defaults: same item means the last two path parts, broken links only; manifest roots count even when the target exists. `living_specs.py check`: exit 0 (areas `aicfg-apply`, `doctor`).

## engine · Plan gate · auto-approved
One task. Callouts: new `repair` state; `--repair` replaces broken links and prunes links into old roots.

## code-reviewer · gh:129 batch · done
Inline (review_context: shared). No CRITICAL/HIGH. Checked that a working link of the user's is never repaired and that `--only` limits repairs like other changes. Changed the expected fix in `DoctorTest.test_broken_link_after_moving_the_repo` (now `apply --repair`) and added the `rm` case for a link to another item.

## engine · verify
799 tests OK (plain and XDG), validate OK (core, acme). The 8 new tests fail on the base code (no `--repair` flag).

## engine · Deliver gate · auto-approved
Push 129-apply-repair, open a ready PR from pr-body.md against 128-brainrc-uninstall ("5 of 6, stacked on #X"; Closes #129). Ticket comment stays a draft. No ticket transition.
