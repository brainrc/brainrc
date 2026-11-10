---
id: 36
title: Plan topic, greeting gaps
status: open
pr:
---
Topic for `/plan` evals: "gaps in the greeting CLI". Run `/plan local:tickets/036-plan-greeting-gaps.md`
in the sandbox (offline). Variants: add `--dry-run` (sandbox-033) or `--oneshot` with a GitHub
target (sandbox-034).

(Expected: the researcher proposes candidates from `greet.py` and `test_greet.py`, each with
an allowlisted proof command such as `grep -n "def greet" greet.py`. One candidate, "greeting
in every language", has no proof and goes under Needs evidence. The run records
`ticket.ref = "local:tickets/036-plan-greeting-gaps.md"` in `specs/plan-greeting-gaps/state.json`.)
