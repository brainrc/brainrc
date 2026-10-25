Shipped: the `watch` stage now handles unresolved PR review threads. Small asks become `R<n>` fix tasks, questions get a drafted reply, design-level asks stop for the user. Embedded instructions are flagged and not followed, and the PR is handed back after 3 rounds.
Replies and pushes wait for one approved Push gate.
Verify: `python3 -m unittest -v tests.test_evals.WatchReviewCommentCaseTest` (sandbox-006 grading, pass and fail folders).
PR: <PR_URL>
