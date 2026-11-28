# Verify: Record the #50 packaging spike

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `docs/harness-packages.md`: at-a-glance table (5 rows), one section per harness with source links, UNCONFIRMED items in bold, evidence notes for Codex, OpenCode, and Cursor | pass |
| AC2 | "What this means" (4 points) and "Proposed order for #50" (6 steps) | pass |
| AC3 | `docs/roadmap.md` links it (and drops the shipped parallel-tasks and plugin items); README layout line; VERSION 0.3.15; CHANGELOG; plugin manifests regenerated after `validate` flagged them stale | pass |
| AC4 | comment drafted in `ticket-comment.md`; posted at Deliver | pending Deliver |

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK; `validate --pack examples/pack-acme` → OK
