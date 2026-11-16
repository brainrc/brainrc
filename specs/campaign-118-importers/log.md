# Campaign gh:118 · importers (E12, Gate A part)

## 2026-11-15T16:20:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:118 --shape ordered --dry-run`

- Members: #163 (CLAUDE.md / AGENTS.md), #164 (Cursor rules), #165 (Copilot instructions), then
  #297 (`init` offers import and a starter profile). All open, none assigned, none skipped.
  #166 (Windsurf) and #167 (Claude plugin) are left for later, per the brief.
- Shape: `playbook` (the epic body names it, with `--batch-size 3`, over `--shape ordered` given
  in the brief). #163, #164 and #165 are rows of the parameter table and share one template;
  #163 seeds it as a normal run, and `playbook.md` is written from it. #297 is not a table row
  (it uses what the three build), so it runs last, as an ordered member.
- Dependency source: `none` (no links between the children); order is the brief's.
- Delivery: one draft PR per child against `main`, each branch stacked on the previous one
  (as in E26, E27 and E28). Merge in order, merging `main` into the next branch first.
- The epic's "start after E7" note is replaced, per the brief: the pack layout is written by one
  small internal writer, `brainrc/scaffold.py`, that `brainrc new pack` (#150) can reuse.
  Old issue bodies name `aicfg/`; the package is `brainrc/`.

## engine · Campaign gate · approved
The coordinator's brief (passing on the maintainer's "Send E12 to coding", a one-shot campaign
like E26) says to dry-run, then build the children in order as draft PRs, each sent to review.
Recorded as approved on that basis; per-child Spec and Plan gates are logged here rather than
stopped on. Merging stays with the maintainer.

## engine · gh:163 · Spec and Plan (seed member, logged under the Campaign gate)
- Spec: `brainrc import PATH ...` reads CLAUDE.md / AGENTS.md and writes a pack: each file split
  at the shallowest heading level used more than once (fence-aware), one `rules/NN-<slug>.md` per
  part in source order, each with a first-line provenance comment (file, line range). A
  whole-line `@path` in CLAUDE.md is replaced by that file's rules; a file already inlined is
  skipped when it comes up again; a brainrc project block is dropped. Output: `--to DIR` or
  `$BRAINRC_HOME/imported/<name>`; refuses a folder with files unless `--force`; validated as
  `validate --pack`; `--enable` writes `packs.local.toml`; `--dry-run` writes nothing.
- Plan: `brainrc/scaffold.py` (render_pack, write_pack), `brainrc/importers/` (`__init__`,
  `model`, `markdown`, `instructions`), `cli.py`, docs/packs.md § Import; fixtures in
  `tests/fixtures/import/instructions/`; tests in `tests/test_importers.py`.

## engine · gh:163 · verified
Draft PR #364 (base `main`). `validate` and the full suite passed before the push.

## engine · gh:164 · Spec and Plan (playbook v1, params: Cursor rules, `.cursor/rules/*.mdc`, rules + globs -> domains)
- Spec: `.cursor/rules/**/*.mdc` in path order, plus `.cursorrules`. `alwaysApply: true` and
  `.cursorrules` become rules (an .mdc file stays one rule: Cursor loads it whole). A rule with
  `globs` becomes a skill whose description ends "Use when working on <globs>", plus an
  `[[extensions.gatework.domains]]` row naming it. A rule with only a description becomes a skill
  with it; one with neither becomes a skill and a warning. Cursor's frontmatter is read line by
  line (`globs: *.py` isn't YAML). Skills with the same name from two sources are numbered, and
  their Domains rows follow.
- Plan: `brainrc/importers/cursor.py`, `FORMATS`, `plan` (rename, keep rows), docs/packs.md row;
  fixtures in `tests/fixtures/import/cursor/`; tests in `tests/test_importers.py`.
- Deviation within the playbook: none.

## engine · gh:164 · verified
Draft PR #365 (base `main`, stacked on #364). `validate` and the full suite passed before the push.

## engine · gh:165 · Spec and Plan (playbook v1, params: Copilot, `.github/copilot-instructions.md`, rules)
- Spec: `.github/copilot-instructions.md` becomes rules, one per section, in order. The
  path-specific `.github/instructions/**/*.instructions.md` files (Copilot's other format, same
  folder) are read too: `applyTo: "**"` becomes a rule; other globs a skill with a Domains row;
  only a description a skill. Order: copilot-instructions.md, then those files in path order.
- Plan: `brainrc/importers/copilot.py`; Cursor's frontmatter and whole-file helpers move to
  `importers/markdown.py`, and the scoped-skill mapping to `Imported.add_skill`, so both formats
  share them; docs/packs.md row; fixtures in `tests/fixtures/import/copilot/`.
- Deviation within the playbook: the path-specific files are beyond the issue's one named
  source; added because the mapping is the one #164 already built.
