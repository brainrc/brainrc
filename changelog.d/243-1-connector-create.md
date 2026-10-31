---
bump: patch
---
- Ticket connectors gain an optional `create` operation, used after an approved Ticket gate: `ticket-local` writes a new ticket file and `ticket-github` opens an issue. A connector without it lists the tickets as drafts for you to create.
