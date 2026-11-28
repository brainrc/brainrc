# Spec: `aicfg doctor`

Ticket: gh:12 · Size: standard (4 files, ~200 lines, design choices below) · Status: draft

## Problem
`status` shows what `apply` would change, but not why an install misbehaves: a stale render
after editing rules, links left dangling by moving the repo, a pack path that's gone, hooks
missing from `settings.json`. Users find out when a skill or rule silently isn't there.

## Goals
- One read-only command that lists every install problem, each with the command that fixes it.

## Non-goals
- Fixing anything (that's `apply`). Checking harness versions or running a model.
- A troubleshooting doc (#17 builds on this).

## Acceptance criteria
- **AC1** Read-only: `doctor` writes nothing, under `HOME` or in the repo, whatever it finds.
- **AC2** Stale render: `dist/instructions.md` missing or different from what `apply` would
  render now → FAIL, fix `apply`. Same for `extensions.md`.
- **AC3** Links, per installed harness: a missing link (FAIL, `apply`), a link pointing at
  the wrong item in the repo (FAIL, `apply`), a stale link `apply` would prune (FAIL, `apply`),
  a broken link whose target is gone, e.g. after moving the repo (FAIL, delete it then
  `apply`), and a real file or a foreign link where a link belongs (FAIL, move it).
- **AC4** Harness not installed: its home directory (the parent of its `instructions` or
  `skills` path, e.g. `~/.codex`) is missing → WARN with the `harnesses.local.toml` line that
  disables it, and its link and settings checks are skipped.
- **AC5** Packs: an enabled pack whose path or `pack.toml` is missing, that core doesn't
  satisfy, or that fails `validate --pack` → FAIL naming the pack and the fix. Doctor still
  runs the other checks with core alone.
- **AC6** Settings: hooks not merged into a harness's `settings.json` → FAIL, `apply`;
  invalid JSON → FAIL, fix by hand.
- **AC7** Python: on Python older than 3.11, every `aicfg.py` command exits with a one-line
  "needs Python 3.11+" message instead of a `tomllib` traceback.
- **AC8** Output: one line per finding (`FAIL` / `WARN`, what, `fix:` command), then a summary.
  Exit 1 on any FAIL, 0 otherwise (WARNs don't fail). With nothing found: `No problems found.`
- **AC9** Documented in the module docstring and README; VERSION 0.3.7 with a CHANGELOG entry.

## Design choices
1. **Missing harness is a WARN, not a FAIL.** `harnesses.toml` enables all five harnesses, and
   few people have all five, so a FAIL would make doctor fail on almost every machine.
2. **The Python check is an import guard, not a doctor line.** `aicfg.py` imports `tomllib`
   at the top, so on 3.10 it crashes before any command runs. A guard around that import
   helps every command; doctor itself can only run on 3.11+.
3. **Reuse `plan()`, `settings_change()`, `render_*()`, and validate**, so doctor and
   `apply` can't disagree about what "in sync" means.

## Constraints
Stdlib only, Python 3.11+. Tests run against a fake `HOME` and a temp repo copy, like the
existing sync tests.

## Open questions
None.
