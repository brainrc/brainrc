# evals

Check workflow runs against expected outcomes offline.

### Campaign check kind
The eval harness SHALL offer a `campaign` check kind that verifies member order and approved spec and plan gates, and for `sequential` delivery first-member-only delivery, for `stacked` delivery every member delivered with a valid base. (AC9)
_Last changed by 090-campaign-ordered-fixes._

### PR status fixture
The sandbox SHALL ship offline `pr_status` fixtures for red CI, review comment, and merged, in the connector return shape, for reuse by later evals. (AC7, AC8)
_Last changed by 078-pr-status-connector._

### Red-CI watch eval
A sandbox eval SHALL grade the CI-failure path offline from the red-CI fixture via `SPEC_PR_STATUS_FIXTURE`, and `state` checks SHALL accept numeric indexes in dotted fields. (AC9, AC10)
_Last changed by 079-watch-ci-failures._

### Review-comment watch eval
A sandbox eval SHALL grade the review-comment path offline from a fixture containing an embedded instruction, which must be flagged and not followed. (AC10)
_Last changed by 080-watch-review-comments._

### Merged watch eval
A sandbox eval SHALL grade the merged path offline from the merged fixture, checking post-merge fields, `verify-merged.md`, and the retro's After delivery section. (AC9)
_Last changed by 081-watch-post-merge._

### Minimum value state check
The eval harness SHALL let a `state` check require a numeric field to be at least a given value, used to require `metrics.understanding.asked` ≥ 1 on sandbox cases 001 and 003. (AC10)
_Last changed by 069-deliver-owner-quiz._

### Plan evals
Sandbox evals and unit tests SHALL grade proven, unprovable, dry-run, oneshot and injection plan cases offline. (AC14)
_Last changed by 243-planning-mode._
