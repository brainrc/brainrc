# Spec: Architecture overview with one diagram

Ticket: gh:14 · Size: small · Status: approved

## Problem
A newcomer has to piece together how `aicfg`, `harnesses.toml`, packs, the spec-agent engine,
agents, and `extensions.md` relate, from five separate docs. There is no single page that shows
what happens at install time versus when an AI tool runs.

## Goals
- One short page a newcomer reads first, linked from the README.

## Non-goals
- Re-documenting details already in `docs/packs.md`, `docs/spec-agent.md`, `docs/formats.md`.
  The page links to them.
- A tutorial (#13).

## Acceptance criteria
- **AC1**: `docs/architecture.md` has one diagram that renders on GitHub: source repos (core,
  packs, `*.local.*` files) → `aicfg apply` (render rules, render extensions, link, merge
  settings) → per-harness directories → at run time, spec-agent reads `extensions.md` and
  dispatches agents and domain skills.
- **AC2**: A "build time vs run time" table says what happens when, and which file each step
  reads or writes.
- **AC3**: A glossary defines harness, core, pack, skill, domain skill, agent, connector, gate,
  and `requires_core`, each in one line with a link to its detailed doc.
- **AC4**: The README links the page near the top. `VERSION` 0.3.2 with a CHANGELOG entry.
  `validate` and tests pass.
- **AC5**: The page stays under ~80 lines and every link resolves.

## Constraints
Generic content only. Prose follows the unslop rules (no semicolons or dashes in prose).

## Open questions
1. **Mermaid or ASCII?** Default: Mermaid. GitHub renders it, and it stays readable as text.
