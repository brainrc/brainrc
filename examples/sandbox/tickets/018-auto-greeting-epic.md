---
id: 18
title: Configurable greetings, auto campaign (epic)
status: open
pr:
children: [local:tickets/007-shout-custom-greeting.md, local:tickets/005-greeting-param.md, local:tickets/006-greeting-flag.md]
---
Run with `/work --campaign local:tickets/018-auto-greeting-epic.md --shape ordered --auto`. The same
three children as ticket 004, listed out of dependency order. Without any new flag, `greet.py`'s
output must not change.

(Expected: no gate stop. The Campaign gate and every child's Spec, Plan, and the stack Deliver
gate are auto-approved, and every child is delivered stacked, in the order 005, 006, 007.)
