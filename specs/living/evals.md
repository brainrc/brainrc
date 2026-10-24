# evals

Check workflow runs against expected outcomes offline.

### Campaign check kind
The eval harness SHALL offer a `campaign` check kind that verifies member order, approved spec and plan gates, and first-member-only delivery. (AC13, AC18)
_Last changed by 074-campaign-ordered-shape._

### Minimum value state check
The eval harness SHALL let a `state` check require a numeric field to be at least a given value, used to require `metrics.understanding.asked` ≥ 1 on sandbox cases 001 and 003. (AC10)
_Last changed by 069-deliver-owner-quiz._
