# Spec: Troubleshooting doc

Ticket: gh:17 · Size: small (new how-to doc, README link, one doctor line) · Status: draft

## Problem
When an install misbehaves, the only help is scattered across the README and `docs/packs.md`.
Uninstalling isn't documented at all, and it has a trap (below).

## Goals
- One how-to page, organised by symptom, each with the exact fix. Doctor points to it.

## Non-goals
- Changing `apply`'s uninstall behaviour (follow-up issue, below).

## Acceptance criteria
- **AC1**: `docs/troubleshooting.md` exists, starts with "run `aicfg doctor`", and covers, by
  symptom: `CONFLICT`; a rule change not taking effect; uninstalling; where settings backups
  live and how many are kept; pack collision and prefix errors (quoting the real messages);
  and a guard hook blocking something safe or missing something risky (how to report it, with
  the near-miss test convention from `tests/test_hooks.py`).
- **AC2**: Every command and file path in it matches the code (`BACKUPS_KEPT`, backup file
  name, error texts), and the uninstall steps were run in a fake `HOME`.
- **AC3**: README links it next to the doctor paragraph; `doctor` ends with a pointer to it
  when it finds anything (test).
- **AC4**: VERSION 0.3.8 with a CHANGELOG entry.

## Finding while writing
Disabling the `claude` harness and running `apply` removes the links and the hooks directory
but leaves ai-config's hook entries in `~/.claude/settings.json`, now pointing at a missing
directory (checked in a fake `HOME`). The doc gives the manual fix. A follow-up issue proposes
that `apply` remove owned hook groups when a harness is disabled, and that `doctor` flag them.
Filing that issue is an outward action, so it's proposed at the Deliver gate.

## Open questions
None.
