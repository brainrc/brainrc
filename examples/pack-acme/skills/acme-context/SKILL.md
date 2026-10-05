---
name: acme-context
description: Adds Acme team context to a spec-agent run at intake (owning team, service tier, related runbooks). Use right after a ticket is fetched, as a spec-agent intake context skill.
---

# acme-context

Run after spec-agent writes `ticket.md`. Append a short `## Acme context` section to it:

1. **Owning team:** from `CODEOWNERS` for the paths the ticket names.
2. **Service tier:** from `deploy/prod.yaml` → `tier` (1 = customer-facing). Tier 1 sets the
   size floor to `standard`.
3. **Runbooks:** links under `docs/runbooks/` for the services involved.

Keep it under 10 lines. Unknown values are written as `unknown`, never guessed.
