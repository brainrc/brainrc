# Log: 130-doctor-plugin-overlap

## engine · intake
gh:130 via ticket-github, child 6 of 6 in campaign gh:109 (`campaign-109-first-run-cli`). `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size small (one doctor check, read-only), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/130-doctor-plugin-overlap`, base `129-apply-repair`. Baseline: 799 tests OK, validate OK.

## engine · Spec gate · auto-approved
3 criteria (AC1–AC3). Defaults: which install to remove differs per harness (Claude: the plugin; Cursor: the links). `living_specs.py check`: exit 0 (area `doctor`).

## engine · Plan gate · auto-approved
One task. No callouts.

## code-reviewer · gh:130 batch · done
Inline (review_context: shared). No CRITICAL/HIGH. The plugin list is read through the same size and parse guards as the old-plugin check. LOW kept: Codex and Antigravity plugins aren't checked, since where they install isn't verified.

## engine · verify
805 tests OK (plain and XDG), validate OK (core, acme). The 6 new tests fail on the base code (no `_double_install_findings`).

## engine · Deliver gate · auto-approved
Push 130-doctor-plugin-overlap, open a ready PR from pr-body.md against 129-apply-repair ("6 of 6, stacked on #X"; Closes #130). Ticket comment stays a draft. No ticket transition.
