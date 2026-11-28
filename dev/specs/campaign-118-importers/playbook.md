# Playbook: one importer per source format

Campaign gh:118 (E12) · shape: playbook · version 1 · seeded by gh:163 (CLAUDE.md / AGENTS.md).

Parameters: `{format}` (the importer's name), `{source}` (the files it reads), `{maps_to}`.

## Steps
1. `brainrc/importers/{format}.py` with `NAMES` (file names `detect` accepts), `LOOK_FOR` when a
   folder holds them somewhere else (`.cursor/rules`), `detect(path)` and `read(path) -> Imported`.
   Register it in `FORMATS` in `brainrc/importers/__init__.py`, in the order `discover` lists it.
2. Map to the scaffold's types only (`Rule`, `Skill`, a Domains row); never write files: `plan`
   joins every source and `brainrc/scaffold.py` renders and writes the pack.
3. Every rule and skill keeps a provenance string, `imported by brainrc from <file>, lines a-b`;
   rules keep source order (markdown bodies go through `importers.markdown.split`).
4. Fixtures in `tests/fixtures/import/{format}/`; tests in `tests/test_importers.py`: the fixture
   imports into a pack that `validate --pack` passes, the rendered rules equal the source text
   in order, and each kind the format has (rule, skill with a Domains row) is covered.
5. docs/packs.md § Import gets a row in its table; one changelog fragment.

## Verification
`python3 scripts/brainrc.py validate`; `python3 -m unittest discover -s tests`.

## Rollback
Remove the module and its `FORMATS` entry; the other formats don't depend on it.

## Review checklist
- Order: rules render in the source's order; NN keeps filename order past nine rules.
- Provenance on every rule and skill, with the right line range.
- No harness-only syntax left in a rule; nothing written outside the pack folder.
- Names meet docs/packs.md § Naming (skills start with the prefix; slugs are ASCII lowercase).
