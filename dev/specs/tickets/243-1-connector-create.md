---
id: 243.1
title: Ticket connectors: a create operation
status: open
pr:
---
Child 1 of 4 of gh:243 (planning mode), split by a `--oneshot` run because the spec sized it `large`.

AC13 of specs/243-planning-mode/spec.md: `ticket-local` and `ticket-github` gain `create` (title, body, optional epic) returning a ref; `validate` accepts connectors with or without `create`; without it the Ticket gate lists drafts only. Unit tests.

Spec: specs/243-planning-mode/spec.md (approved; Proposed split item 1).
