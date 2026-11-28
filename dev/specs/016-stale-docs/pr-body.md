Fix stale docs and state per-harness support in the README

## Why
Three docs said things that are no longer true or described one machine. The README promised every content type syncs into every harness, which sets the wrong expectation on the first paragraph.

## What changed
- README opening says what actually syncs: skills everywhere, rules, commands, and agents only in some harnesses so far, guard hooks Claude Code only, MCP not synced yet. It links the harness support table.
- `docs/spec-agent.md` names the existing ticket connectors instead of calling Jira planned.
- `docs/efficiency.md` drops "Already installed here" from the caveman row.
- CHANGELOG Unreleased entry. The roadmap item in the issue was already done by #5.

Blast radius: docs only.

## Acceptance criteria
- [x] AC1: spec-agent.md names existing connectors
- [x] AC2: no machine-specific wording in efficiency.md
- [x] AC3: README states per-harness reach and links the table
- [x] AC4: roadmap Done item confirmed done by #5
- [x] AC5: tests and `validate` pass, no stale wording left

## How to verify
```
grep -rn "planned next\|installed here" docs README.md   # no output
python3 scripts/aicfg.py validate
```

## Follow-ups
- none

Spec: `specs/016-stale-docs/spec.md` · Plan: `specs/016-stale-docs/plan.md`
Closes #16

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
