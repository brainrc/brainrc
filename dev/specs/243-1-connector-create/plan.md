# Plan: Ticket connectors: a create operation

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** none (an optional connector operation; existing connectors unaffected)
- **Migrations / data changes:** none
- **Security triggers touched:** outward action wording (create after the Ticket gate); shell handling of untrusted titles
- **Domains:** none
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Add a `create` row to the connector contract, a `## create` section to ticket-local and ticket-github, and tests that both document it and that a connector without it still validates.

## Files
| File | Change |
|---|---|
| `skills/spec-agent/references/connectors.md`, `skills/ticket-local/SKILL.md`, `skills/ticket-github/SKILL.md`, `tests/test_brainrc.py`, `changelog.d/243-1-connector-create.md` | modify / new |

## Risks
- Untrusted titles reaching a shell: mitigated by reading titles from files into variables.

## Test strategy
Unit tests in tests/test_brainrc.py (ConnectorCheckTest); validate.

## Tasks
- [x] **T1** [agent: engine] create operation in the contract and two connectors
  - files: as in Files
  - criteria: AC1, AC2
