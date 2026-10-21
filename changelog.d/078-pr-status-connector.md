---
bump: patch
---
- Connector contract gains an optional read-only `pr_status` operation (head checks, unresolved review threads, merge state; thread text fenced as untrusted). A connector without it makes `watch` skip. `ticket-github` implements it (read-only `gh` and GraphQL calls), and offline `pr_status` fixtures (red CI, review comment, merged) ship in `examples/sandbox/`.
