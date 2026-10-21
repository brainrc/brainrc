---
bump: patch
---
- Add the `ordered` campaign shape (children built and merged in dependency order), the `--shape` flag, and a `dependencies` connector op (ticket-github, ticket-local).
- Document campaign shapes in docs/spec-agent.md and the `campaign` eval check kind in docs/evals.md.
- Add a sandbox epic (`004-greeting-epic`) with out-of-order children to try the ordered shape.
