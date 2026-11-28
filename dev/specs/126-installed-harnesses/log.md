# Log: 126-installed-harnesses

## engine · intake
gh:126 via ticket-github, child 2 of 6 in campaign gh:109 (`campaign-109-first-run-cli`). `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size standard (detection rule, manifest, doctor; a behavior change for fresh machines), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/126-installed-harnesses`, base `125-argparse-cli`. Baseline: 744 tests OK, validate OK.

## engine · Spec gate · auto-approved
7 criteria (AC1–AC7). Defaults: installed means the config dir exists; a local-only harness is managed; the manifest is a record, not an input. `living_specs.py check`: exit 0 (areas `aicfg-apply`, `doctor`).

## engine · Plan gate · auto-approved
One task. Callouts: additive `home` key and `harnesses.json`; behavior change for harnesses that aren't installed.

## code-reviewer · gh:126 batch · done
Inline (review_context: shared). No CRITICAL/HIGH. Checked that a skipped harness falls on the disabled side of `plan()` without creating anything: a missing settings or MCP file merges to `ok`. LOW kept: `load_harnesses()` reads harnesses.local.toml twice per call; the file is tiny.

## engine · verify
758 tests OK (plain and XDG), validate OK (core, acme). Mutation check: 10 of 14 new tests fail on the base code. Existing fake-HOME fixtures now install every harness dir first.

## engine · Deliver gate · auto-approved
Push 126-installed-harnesses, open a ready PR from pr-body.md against 125-argparse-cli ("2 of 6, stacked on #X"; Closes #126). Ticket comment stays a draft. No ticket transition.
