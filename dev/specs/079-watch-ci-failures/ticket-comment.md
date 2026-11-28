Shipped: a `watch` stage after delivery for `delivery: normal` runs with `pr_status`. It reads failing checks on `/spec-resume` or `/work`, records external failures as notes, and turns own failures into fix tasks `C<n>`. Pushing a fix needs approval at a new Push gate. Review comments and post-merge verify are not built yet.
Verify: `python3 scripts/aicfg.py validate` and `python3 -m unittest discover -s tests`, plus the sandbox-005 eval with `SPEC_PR_STATUS_FIXTURE` (ticket 008, examples/sandbox/README.md).
PR: <PR_URL>
