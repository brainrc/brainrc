---
bump: patch
---
- `/plan <topic>` (spec-agent planning mode): a new `researcher` role investigates a topic and proposes candidate tickets, each with runnable proof (a command and its output, a failing test, or a local spike commit) and `file:line` links. The engine re-runs every proof; unproven candidates go under "Needs evidence". Web research only with `--web`, and the researcher never follows instructions found in content.
