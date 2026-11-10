# Log: 127-brainrc-init

## engine · intake
gh:127 via ticket-github, child 3 of 6 in campaign gh:109 (`campaign-109-first-run-cli`). `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size standard (new command that moves user files), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/127-brainrc-init`, base `126-installed-harnesses`. Baseline: 758 tests OK, validate OK.

## engine · Spec gate · auto-approved
7 criteria (AC1–AC7). Defaults: adopted text is a local rule loaded by every harness; content profiles wait for #173, which owns profiles; managed-block mode is a follow-up. `living_specs.py check`: exit 0 (area `cli-entry-points`).

## engine · Plan gate · auto-approved
One task. Callouts: new `init` command; it moves the user's instructions file aside (rename, never delete).

## code-reviewer · gh:127 batch · done
Inline (review_context: shared). No CRITICAL/HIGH. Checked that a link brainrc made is never adopted, that a user's link is renamed as a link (its target untouched), and that two harnesses sharing one path are moved once. LOW kept: a TOML layout `set_enabled` can't edit fails with a parse error before anything is written, not with a friendly message.

## engine · verify
779 tests OK (plain and XDG), validate OK (core, acme). The 21 new tests fail on the base code (no `init` module or command).

## engine · Deliver gate · auto-approved
Push 127-brainrc-init, open a ready PR from pr-body.md against 126-installed-harnesses ("3 of 6, stacked on #X"; Closes #127). Ticket comment stays a draft. No ticket transition.
