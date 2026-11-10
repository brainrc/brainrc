# Log: 125-argparse-cli

## engine · intake
gh:125 via ticket-github, child 1 of 6 in campaign gh:109 (`campaign-109-first-run-cli`). `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size standard (four modules, a real design choice for `--only`), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/125-argparse-cli`, base `main`. Baseline: 729 tests OK, validate OK.

## engine · Spec gate · auto-approved
7 criteria (AC1–AC7). Defaults: a harness outside `--only` is untouched even if disabled; rules still render; `--version` with a command is a usage error. `living_specs.py check`: exit 0 (area `cli-entry-points`).

## engine · Plan gate · auto-approved
One task. Callouts: additive contract change only (`--help` exits 0, new `--only`).

## code-reviewer · gh:125 batch · done
Inline (review_context: shared). No CRITICAL/HIGH. Fixed before commit: a broken harnesses.toml under `--only` exited 2 instead of 1 (MEDIUM), now the same as without `--only`, with a test. LOW kept: the formatter that hides commands reads argparse's private `_choices_actions`, present in 3.11 to 3.13.

## engine · verify
744 tests OK (plain and XDG), validate OK (core, acme). Mutation check: 14 of 15 new tests fail on the base code.

## engine · Deliver gate · auto-approved
Push 125-argparse-cli, open a ready PR from pr-body.md against main (Closes #125). Ticket comment stays a draft. No ticket transition.
