---
id: 149.1
title: Namespaced core skills with deprecated aliases
status: open
pr:
---
Child 1 of 3 of gh:149 (namespace core skills), split by a `--oneshot` run because the spec sized it `large`. Campaign gh:113 child 4.

AC1, AC2, AC3, AC8 of specs/149-namespace-core-skills/spec.md: ship `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws`, `brainrc-terraform`; the old names stay as deprecated aliases for one minor release that say so, name the replacement and the removal release, and never double an auto-trigger; the plugin build carries both. Unit tests.

Spec: specs/149-namespace-core-skills/spec.md (approved; Proposed split item 1).
