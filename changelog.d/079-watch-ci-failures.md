---
bump: patch
---
- spec-agent gains a `watch` stage after delivery: on `/spec-resume` it reads the PR's checks, records failures it can't attribute to the diff as `external`, and turns own failures into fix tasks `C<n>` that run through the normal review loop. Pushing a fix needs approval at a new Push gate. `SPEC_PR_STATUS_FIXTURE` lets offline evals supply `pr_status`. Review comments and post-merge verify remain planned.
