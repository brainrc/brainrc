---
id: 4
title: Configurable greetings (epic)
status: open
pr:
children: [local:tickets/007-shout-custom-greeting.md, local:tickets/005-greeting-param.md, local:tickets/006-greeting-flag.md]
---
Make the greeting configurable in three steps. The children are listed out of dependency
order on purpose: spec-agent should order them by `depends_on` (005, 006, 007), not by this list.
Without any new flag, `greet.py`'s output must not change.
