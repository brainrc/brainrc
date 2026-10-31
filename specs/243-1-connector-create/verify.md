# Verify: Ticket connectors: a create operation

Run at 2026-10-31T20:23:46Z on commit `9cbf95e`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: OK (1 skipped) |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_core_local_and_github_connectors_document_create`: both connectors have `## create`, list it in their Implements line, and the contract row is optional and outward; the title is read from a file (ticket-github), the slug is `[a-z0-9-]` (ticket-local). The connector command itself was not run (no tracker in a test). | pass (instruction text and heading test) |
| AC2 | `test_a_connector_without_create_still_validates`; contract row states the drafts fallback | pass |

## Notes
Code review: 2 HIGH (title shell interpolation; no epic on the gh path) and 4 MEDIUM, 1 LOW, all fixed in 9cbf95e.
