Moved the `validate` and `release` workflows off Node 20: `actions/checkout` is now v7.0.1 and `actions/setup-python` is v7.0.0, both full-SHA pinned. Workflow inputs and behavior are unchanged.
To verify: the `validate` job log has no "Node.js 20 is deprecated" warning, and the first post-merge `release` run is green with its tag and GitHub Release present.
PR: <PR_URL>
