# Log: 128-brainrc-uninstall

## engine · intake
gh:128 via ticket-github, child 4 of 6 in campaign gh:109 (`campaign-109-first-run-cli`). `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size standard (new command that removes files), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/128-brainrc-uninstall`, base `127-brainrc-init`. Baseline: 779 tests OK, validate OK.

## engine · Spec gate · auto-approved
7 criteria (AC1–AC7). Defaults: no confirmation prompt (dry run, backups); emptied files become backups; local config stays without `--purge`. `living_specs.py check`: exit 0 (area `aicfg-apply`).

## engine · Plan gate · auto-approved
One task. Callouts: removes what brainrc owns; `--purge` deletes `$BRAINRC_HOME`.

## code-reviewer · gh:128 batch · done
Inline (review_context: shared). No CRITICAL/HIGH. Checked that only links with a brainrc target are removed (a user's own link in `~/.claude/skills` stays), that a harness home is never removed, and that settings and MCP go through the same merge code as a disabled harness. LOW kept: `--purge` removes the settings home while holding its `apply.lock`, which is fine on Linux and macOS; native Windows is #120's.

## engine · verify
790 tests OK (plain and XDG), validate OK (core, acme). The 11 new tests fail on the base code (no `uninstall` module or command).

## engine · Deliver gate · auto-approved
Push 128-brainrc-uninstall, open a ready PR from pr-body.md against 127-brainrc-init ("4 of 6, stacked on #X"; Closes #128). Ticket comment stays a draft. No ticket transition.
