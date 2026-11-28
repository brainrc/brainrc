# Spec: living specs: each run updates a per-area statement of current behavior

Ticket: gh:23 (closes) · Size: standard (workflow change across spec-agent docs, a script, tests, a sandbox run) · Status: draft

## Problem
Each `specs/<slug>/` describes one change. Nothing records how the system behaves now, so
every analyst re-derives it from code, and nothing catches a new spec that contradicts an
old one. OpenSpec solves this with per-capability truth files that changes update by delta.

## Acceptance criteria
- **AC1 Truth files.** `specs/living/<area>.md`, one per capability area (e.g. `export`, `cli`;
  not the stack skills spec-agent calls domains): a one-line purpose, then `### <requirement>`
  blocks of SHALL statements, each naming the run that last changed it. Format in
  `templates/living.md`; `state.md` documents the layout.
- **AC2 Deltas.** The spec template gains `## Requirement changes`: per area, `ADDED`,
  `MODIFIED` (full new text), and `REMOVED` (with why) requirement blocks, tied to ACs. A run
  that changes no behavior writes `None`.
- **AC3 Analyst.** At the spec stage the analyst lists `specs/living/`, reads only the areas the
  ticket touches, and writes the delta against them; a MODIFIED or REMOVED name must exist.
  The architect and verifier need no changes.
- **AC4 Apply step.** In the document stage (so the Deliver gate's diff shows it), the engine runs
  `python3 <skill>/scripts/living_specs.py apply specs/<slug>/spec.md`. It is stdlib-only and
  edits the area files; an unknown MODIFIED or REMOVED target, a duplicate ADDED, or a malformed
  section fails with nothing written. `check` does the same without writing. Without Python, the
  doc-writer applies the delta by hand with the same rules. The run folder stays where it is;
  `state.json` records `living: [areas]`. `lifecycle.md` defines the step.
- **AC5 Tests.** `tests/test_living_specs.py`: add, modify, remove across two areas, each failure
  case, idempotence (applying the same spec twice is an error, not a duplicate), and a new area
  file created on first ADDED. Two sequential sandbox tickets (001 then 003), run inline:
  run 2's spec MODIFIES a requirement run 1 ADDED, and the truth file reflects both.
  `evals/cases/sandbox-001.toml` checks the area file exists.
- **AC6 Docs.** `docs/spec-agent.md` section with credit to OpenSpec, roadmap, CHANGELOG,
  VERSION 0.3.28.

## Open choices
1. **Where truth lives.** (A, recommended) `specs/living/<area>.md`: one flat folder, apart from
   run folders. (B) `specs/<area>/spec.md` as the issue words it: area folders would sit among
   `NNN-slug` run folders and need a naming rule to tell them apart.
2. **Who applies deltas.** (A, recommended) The script: deterministic and tested; hand-apply only
   without Python. (B) The doc-writer always edits the files by hand: no script, but no checks.

## Not in this step
Back-filling truth from past runs, cross-area renames, and moving run folders to an archive.
