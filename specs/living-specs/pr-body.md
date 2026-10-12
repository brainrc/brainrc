## Summary
spec-agent now keeps **living specs**, after OpenSpec (closes #23): `specs/living/<area>.md` records how each capability area behaves now, and every run updates it with a delta.

- **Delta in the spec:** `spec.md` gains `## Requirement changes`: per area, `ADDED`, `MODIFIED` (full new text) and `REMOVED` (with a `Why:`) requirements tied to ACs, or `None.`
- **Analyst:** lists `specs/living/`, reads only the areas the ticket touches, and writes the delta against them. A ticket that contradicts a living requirement becomes a MODIFIED block plus an open question.
- **Apply step:** in the document stage the engine runs `skills/spec-agent/scripts/living_specs.py apply specs/<slug>/spec.md`, so the Deliver gate's diff shows the behavior change next to the code.
  - The script checks every block first: a MODIFIED or REMOVED target must exist, an ADDED one must not, and a new area needs a `Purpose:`. If any block fails, nothing is written.
  - It's stdlib-only, and `check` validates without writing.
  - Without Python, the doc-writer applies the delta by hand.
- **Format:** each requirement ends with `_Last changed by <slug>._`. Run folders stay where they are, and `state.json` records the areas a run changed in `living`.
- **Not covered:** back-filling truth from past runs, and renames across areas.
- `VERSION` 0.3.28.

## Acceptance criteria
- [x] AC1 truth files and template
- [x] AC2 delta section in the spec template
- [x] AC3 analyst reads the living specs
- [x] AC4 apply step in `lifecycle.md`
- [x] AC5 tests and two sequential sandbox tickets
- [x] AC6 docs and OpenSpec credit

## Testing
- `python3 -m unittest discover -s tests` → OK (210, 9 new in `tests/test_living_specs.py`).
- **Sandbox, two tickets in a row** (inline, in a scratch copy):
  - Ticket 001 created `specs/living/cli.md`.
  - After merging it, ticket 003's spec MODIFIED a requirement 001 had ADDED, added another, and created a `farewell` area.
  - Re-applying 001's spec failed and wrote nothing.
  - `sandbox-001` eval: 11/11 before the merge. Its two new living-spec checks pass. The only failure after the merge is `main_untouched`, which this two-run setup trips on purpose.
- `validate` (core and pack) → OK.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
