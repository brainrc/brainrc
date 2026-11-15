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

## engine · gh:165 · verified
Draft PR #366 (base `main`, stacked on #365). `validate` and the full suite passed before the push.

## engine · gh:297 · Spec and Plan (ordered member, logged under the Campaign gate)
- Spec: `init` decides everything first, then shows counts, then (when it asks) waits for a yes,
  then writes. Run from a folder that isn't HOME or a brainrc checkout, it finds the folder's
  CLAUDE.md, AGENTS.md, Cursor and Copilot files (`importers.discover`, minus any file it adopts)
  and offers to import them into pack `imported` at `$BRAINRC_HOME/imported/imported`, added to
  packs.local.toml. The question defaults to no, since the pack loads in every session; `--yes`
  names the files and imports nothing; `--import` imports without asking. An earlier import is
  left alone. A starter profile (`--starter`, or a question defaulting to `app`) writes
  `profile` and `exclude`: minimal -> minimal; app -> recommended minus Gatework's Terraform,
  AWS, Kubernetes and GitOps skills; infra -> full. Switching starters keeps the user's own
  patterns. Counts: files new / changed / moved aside; hooks per harness from the sources'
  settings fragments under the new profile; tokens of rules (core, packs, local, adopted,
  imported) plus the descriptions the profile installs after `exclude`. Packs not fetched yet are
  named as not counted.
- Plan: `brainrc/starter.py` (new), `brainrc/init.py`, `cli.py` (`--starter`, exclusive with
  `--profile`; `--import`), docs/install.md; tests in `tests/test_init_import.py`.
- Starter profiles and their excludes are this campaign's own default (the issue names the three
  profiles but not what each holds); listed for the maintainer.

## engine · gh:297 · verified
Draft PR #367 (base `main`, stacked on #366). `validate` and the full suite passed before the push.

## engine · review · code-review (high) on each PR's own diff
Each PR was reviewed on its increment over the PR below it, fixed on its own branch, and merged
forward (no force-push). `validate` and the full suite passed before every push.
- #364 (gh:163): 10 found, 10 fixed. `--force` replaces only an earlier pack (never a link or a
  folder holding a source) through a backup swap; @imports inline into one text before splitting;
  one fence reader; order-independent skip; `--enable` turns a disabled pack on, writes atomically
  and `~`-relative; unreadable or non-UTF-8 sources fail with a message; CLAUDE.local.md is not
  discovered; one TOML table helper.
- #365 (gh:164): 10 found, 10 fixed. Frontmatter through brainrc's YAML-subset reader (block
  lists, folded text, quotes, BOM); brace-aware globs; same-named rules in one folder keep their
  rows; order numbers leave folder names; empty `.cursorrules` warns; `--format` with a folder.
- #366 (gh:165): 10 found, 10 fixed. `applyTo` with any of `**`/`**/*` is a rule and `*` is not;
  `excludeAgent: coding-agent` skipped; `--format copilot` on another file reads it as repo-wide;
  shared folder walk; the changelog and docs name nested files.
- #367 (gh:297): 10 found, 9 fixed, 1 no change. Starter asked only when no profile is set; pack
  folder checked before asking, pack written and validated first; managed links not offered;
  `--import` says why when empty; turned-on default packs counted; TOML-aware `exclude` edit;
  `session_tokens` renders as `brainrc tokens` does; one prompt and one write loop. No change: a
  bad profile line was already refused by `check_config` before this PR.

