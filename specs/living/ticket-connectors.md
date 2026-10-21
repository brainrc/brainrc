# ticket-connectors

Read and update tickets through a uniform connector contract.

### Dependencies read
A connector SHALL offer a read-only `dependencies` operation for campaign ordering; `ticket-local` reads `depends_on:`; `ticket-github` uses the dependency API with a `Depends on #N` body fallback and reports the source used. (AC5, AC16)
_Last changed by 074-campaign-ordered-shape._
