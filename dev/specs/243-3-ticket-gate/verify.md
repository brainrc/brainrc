# Verify: Ticket gate, dry run, cap and oneshot

Run at 2026-10-31T23:57:59Z on commit `6c55703`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: OK (1 skipped); TicketGateTest 8 tests |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC4 | planning.md § Ticket gate: `--dry-run` wins over every flag and never calls create; test_dry_run_creates_nothing, test_auto_alone_never_approves_and_dry_run_wins | pass (instruction text) |
| AC5 | the gate lists each ticket as an outward action and nothing is created until approval; test_gate_lists_each_ticket_as_an_outward_action | pass (instruction text) |
| AC6 | gates.ticket and metrics.gates.ticket recorded; created refs in state.json; test_gate_is_recorded_like_other_gates | pass (instruction text) |
| AC7 | --oneshot: proven local tickets only, `github create refused`; --auto alone never approves; test_oneshot_creates_local_tickets_only | pass (instruction text) |
| AC10 | at most 10 offered, the rest deferred; test_cap_and_deferred | pass (instruction text) |

## Notes
Security review: 1 HIGH (`--auto` alone approved the gate), 2 MEDIUM, 3 LOW, fixed in edaea03. The re-review found no CRITICAL or HIGH; its 2 LOWs are fixed in 6c55703. No real /plan run.
