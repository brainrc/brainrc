# ticket-connectors

Read and update tickets through a uniform connector contract.

### Dependencies read
A connector SHALL offer a read-only `dependencies` operation for campaign ordering; `ticket-local` reads `depends_on:`; `ticket-github` uses the dependency API with a `Depends on #N` body fallback and reports the source used. (AC5, AC16)
_Last changed by 074-campaign-ordered-shape._

### Pull request status read
A connector MAY offer a read-only `pr_status` operation returning head-commit check results, unresolved review threads (author and body, untrusted), and merge state; `ticket-github` SHALL implement it; `validate` SHALL accept connectors with or without it; a connector without it SHALL make `watch` skip so the run ends at `done`. (AC1, AC2, AC3, AC4, AC5, AC6)
_Last changed by 078-pr-status-connector._

### Ticket create operation
A connector MAY offer a `create` operation (title, body, optional epic) returning a ref; `ticket-local` and `ticket-github` SHALL implement it, and `validate` SHALL accept connectors with or without it. (AC13)
_Last changed by 243-planning-mode._
