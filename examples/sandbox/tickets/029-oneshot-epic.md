---
id: 29
title: Configurable greetings, oneshot campaign (epic)
status: open
pr:
children: [local:tickets/007-shout-custom-greeting.md, local:tickets/005-greeting-param.md, local:tickets/006-greeting-flag.md]
---
Run with `/work --campaign local:tickets/029-oneshot-epic.md --shape ordered --oneshot`. The same
three children as ticket 004, listed out of dependency order. Without any new flag, `greet.py`'s
output must not change.

(Expected: no gate stop. Every child is delivered stacked, in the order 005, 006, 007, and every
PR is ready, not draft.)
