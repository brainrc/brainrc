Add an architecture overview with one diagram and a glossary

## Why
A newcomer had to piece together how `aicfg`, `harnesses.toml`, packs, the spec-agent engine, agents, and `extensions.md` relate from five separate docs.

## What changed
- `docs/architecture.md`: one Mermaid diagram (sources → `aicfg apply` → per-harness directories → spec-agent at run time), a table of what happens at install time vs run time and which files each step reads and writes, and a glossary of nine terms linked to their detailed docs.
- The README links it under the intro.
- `VERSION` 0.3.2.

Blast radius: docs only.

## Acceptance criteria
- [x] AC1: one diagram covering install and run time
- [x] AC2: install vs run time table
- [x] AC3: glossary with links
- [x] AC4: README link, 0.3.2, checks pass
- [x] AC5: 54 lines, links resolve

## How to verify
Open `docs/architecture.md` on this PR and check the diagram renders.

## Follow-ups
- none

Spec: `specs/014-architecture-overview/spec.md` · Plan: `specs/014-architecture-overview/plan.md`
Closes #14

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
