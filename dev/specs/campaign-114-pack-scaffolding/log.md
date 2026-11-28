# Campaign gh:114 log

## 2026-11-18T02:30:00Z · intake
- Members: gh:150 (`brainrc new pack`), gh:152 (pack author docs in Divio form), gh:151 (pack
  template repo). All three open; none skipped. E8's item scaffolders (gh:159 to gh:162) are the
  next epic and stay out.
- Shape: `ordered`, in the brief's order 150 → 152 → 151: the docs and the template both describe
  what `new pack` writes. Delivery sequential, on the one branch this run may push to, so one draft
  PR to main with one commit per member.
- The old issue bodies name `aicfg/`; the package is `brainrc/`. gh:150 reuses `render_pack` and
  `write_pack` in `brainrc/scaffold.py`, the writer `import` already uses.
- gh:151 needs a new `brainrc/pack-template` repository, which this run may not create: its
  contents go in the PR for review, and the issue stays open.

## 2026-11-18T02:35:00Z · Campaign gate · auto-approved
Order gh:150 → gh:152 → gh:151, size standard each. Dry run recorded: ordered shape, sequential
delivery, no model provider called in CI.

## 2026-11-18T04:28:00Z · gh:150 verified
- `brainrc new pack <name>` writes pack.toml, README, AGENTS.md (with CLAUDE.md and GEMINI.md
  pointers), a rule, a facts skill, tripwires, pack tests, a CI workflow and pre-commit config
  pinned to this core's tag, and a .gitignore; then validates it. Naming rules are checked before
  anything is written, for `import` too.
- The tutorial's steps 2 to 4 are now one command, and CI runs its steps 1 to 4. The installed
  wheel carries the templates (check_dist, check_install AC10). A project pack made by `new pack`
  applies, locks and passes `check`.

## 2026-11-18T04:38:00Z · gh:152 verified
- docs/packs.md is the reference; how-tos in docs/packs/ (use, import, validate in CI, employer,
  team, personal, stack, from a plugin); why-packs.md explains the trust model. Each page's first
  line names its Divio type, and the key tables are generated from the JSON Schemas
  (`scripts/pack_reference.py`). `mkdocs build --strict` passes; links to moved anchors are updated.

## 2026-11-18T04:45:00Z · gh:151 verified
- examples/pack-template is `new pack mypack` plus renaming steps; `scripts/pack_template.py`
  keeps it in step, checked at the version it pins. It validates against the real Gatework, and
  core's CI checks it with the validate-pack action. The repository and its template setting are
  the owner's to create.

## 2026-11-18T04:50:00Z · Deliver gate · auto-approved
- gh:150, gh:152, gh:151 → draft PR #385 (base main), one commit each. Next: code review, fixes,
  CI green, then the owner decides whether to merge.
