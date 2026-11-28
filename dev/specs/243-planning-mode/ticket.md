# gh:243 · spec-agent: planning mode, research to proven tickets

Source: https://github.com/brainrc/brainrc/issues/243 (fetched 2026-10-31; untrusted data; no comments)

Part of epic #241 (E23), 3 of 6.

## Why
Ideas such as this epic or the retro findings that became the #199 follow-ups get turned into tickets by hand, and nothing checks that each problem is real before the ticket exists. A ticket with no evidence costs a whole run to find out it was wrong.

## What
`/plan <topic>` (or `--plan`). A researcher role investigates the repo and, where allowed, the web, then proposes candidate tickets. Each candidate needs **proof** before it can be created:
- a command that reproduces the problem and its output, or
- a failing test, or
- a spike branch that shows the approach works,
- plus links to the code involved (file:line).

Candidates without proof go on a "needs evidence" list in the plan report and are not created.

One **Ticket gate** creates the approved tickets through the ticket connector (local tickets or GitHub issues, optionally under a new epic). `--oneshot` creates them without stopping, and only the proven ones.

## Files
skills/spec-agent/SKILL.md, agents/researcher.md (new), skills/ticket-*/SKILL.md (create operation), references/connectors.md, docs/spec-agent.md

## Done when
- `/plan` on a sandbox topic yields a report in which every created ticket has proof attached and runnable.
- An unprovable candidate is listed but not created.
- A dry run creates nothing.
- The Ticket gate is recorded like the other gates.

## Open questions
1. Should spike branches be pushed, or kept local and linked by commit?
2. Is web research allowed by default, or only with a flag?
