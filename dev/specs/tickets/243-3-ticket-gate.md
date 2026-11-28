---
id: 243.3
title: Ticket gate, dry run, cap and oneshot
status: open
pr:
---
Child 3 of 4 of gh:243 (planning mode), split by a `--oneshot` run because the spec sized it `large`.

AC4, AC5, AC6, AC7, AC10 of specs/243-planning-mode/spec.md: the Ticket gate lists tickets as outward actions, `--dry-run` creates nothing, the gate is recorded like the others, `--oneshot` auto-approves and creates local tickets only (GitHub refused, `github create refused` logged), cap 10 with the rest deferred.

Spec: specs/243-planning-mode/spec.md (approved; Proposed split item 3).
