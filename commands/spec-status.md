---
description: Show spec-agent progress for the current branch or a given ticket
argument-hint: [ticket ref or slug]
---

Read `specs/*/state.json` for $ARGUMENTS (default: the spec whose `branch` is the current
git branch; if none, list all specs with their stage). Report in at most 8 lines: ticket,
size/mode, stage, gate status, tasks done/total, blocked reason if any, and the next action.
Do not change anything.
