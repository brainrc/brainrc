# Verify: Fix stale docs and align the README pitch with harness support

Run at 2026-10-05T13:43:27Z on commit `bce1a9a`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 47 tests |
| Validate | `python3 scripts/aicfg.py validate` | pass |
| Stale wording | `grep -rn "planned next\|installed here" docs README.md` | none |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `docs/spec-agent.md` Extending names `ticket-local`, `ticket-github`, `ticket-jira` | pass |
| AC2 | `docs/efficiency.md` caveman row: "Little effect on tool-heavy runs" | pass |
| AC3 | README opening: skills everywhere, rules/commands/agents only some, hooks Claude Code only, MCP not synced; links `docs/formats.md#harness-support` (heading exists) | pass |
| AC4 | `docs/roadmap.md` already links the CHANGELOG (done in #5) | pass |
| AC5 | tests and validate pass; grep finds no other stale wording | pass |
