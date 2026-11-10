# Log: 104-local-tripwires

## engine · intake
gh:104 via ticket-github, child 1 of 3 in campaign gh:94 (`campaign-094-neutral-core`). `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size small (validate.py plus tests and two doc lines; no new dependency, no contract change), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/104-local-tripwires`, base `main`. Baseline: 703 tests OK, validate OK.

## engine · Spec gate · auto-approved
6 criteria (AC1–AC6). Defaults: literal case-insensitive terms; walk without git; the error names the term. `living_specs.py check`: exit 0 (new area `validate`). Plan stage skipped (small): one-task plan written by the engine.

## code-reviewer · gh:104 batch · done
Inline (review_context: shared). No CRITICAL/HIGH/MEDIUM. 1 LOW: a tracked symlink to a directory skips the file-name check (it is not a file); kept, no core symlink names a person or company.

## engine · verify
712 tests OK (plain and XDG), validate OK (core, acme). Mutation check: 5 of 9 new tests fail on the base validate.py.

## engine · Deliver gate · auto-approved
2026-11-10T06:11:42Z
Push 104-local-tripwires, open a ready PR from pr-body.md against main (Closes #104). Ticket comment stays a draft. No ticket transition.

## engine · watch · review on #263
One inline finding (bxker): the new git tests inherit a pre-commit hook's GIT_DIR / GIT_INDEX_FILE and stage temp files into the real index. Reproduced (84 files staged, 2 failures), fixed in LocalTripwireTest.setUp by dropping GIT_* for each test; reproduced again: 0 staged, 9 pass. The pre-existing GitPackTest issue is left as a follow-up for the owner.
