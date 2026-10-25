Shipped: optional, read-only `pr_status` connector operation. The contract is in `skills/spec-agent/references/connectors.md`. `ticket-github` implements it with `gh pr view` and one GraphQL call, and writes nothing. Offline fixtures for red CI, review comment, and merged are in `examples/sandbox/pr_status/`.
Verify: `python3 scripts/aicfg.py validate` and `python3 -m unittest discover -s tests`.
PR: <PR_URL>
