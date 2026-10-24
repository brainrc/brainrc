# evals

Check workflow runs against expected outcomes offline.

### Campaign check kind
The eval harness SHALL offer a `campaign` check kind that verifies member order, approved spec and plan gates, and first-member-only delivery. (AC13, AC18)
_Last changed by 074-campaign-ordered-shape._

### PR status fixture
The sandbox SHALL ship offline `pr_status` fixtures for red CI, review comment, and merged, in the connector return shape, for reuse by later evals. (AC7, AC8)
_Last changed by 078-pr-status-connector._
