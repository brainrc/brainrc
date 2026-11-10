# Spec: Ticket connectors: a create operation

Ticket: local:specs/tickets/243-1-connector-create.md · Size: small · Status: approved

## Problem
Planning mode (gh:243) must create proven tickets after its Ticket gate, but no connector has an operation for creating a ticket.

## Goals
- `ticket-local` and `ticket-github` document an optional, outward `create` operation that returns a ref.

## Non-goals
- The Ticket gate itself and `/plan` (children 243.2 and 243.3).
- `ticket-jira` (it keeps the drafts fallback).

## Acceptance criteria
- **AC1**: Given `ticket-local` and `ticket-github`, when `create` is called with a title, a body file and an optional epic, then each returns a ref (`local:specs/tickets/<NNN>-<slug>.md`, `gh:<number>`), and neither pastes the title or body into a shell string.
- **AC2**: Given a connector with or without `create`, when `validate` runs, then both pass; a connector without it makes the Ticket gate list drafts only (connectors.md).

## Constraints
`create` is outward and runs only after an approved Ticket gate. Untrusted text is never quoted into a created body.

## Requirement changes
None. The parent spec (specs/243-planning-mode/spec.md) holds the ticket-connectors requirement; it is applied when the campaign delivers.

## Open questions
None.

## Proposed split
Not applicable.
