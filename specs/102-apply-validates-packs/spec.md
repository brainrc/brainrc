# Spec: apply validates packs before linking

Ticket: gh:102 · Size: small · Status: draft

## Problem
`validate` and `validate --pack` check each pack's items (name prefix, frontmatter, references,
hook fragments, tripwires), but `status` and `apply` don't. A pack with a skill missing its
prefix (`deploy` instead of `acme-deploy`) is linked into every harness and `apply` exits 0;
only a later `validate` or `doctor` says it was wrong, after the unprefixed name is already in
the user's harness and may shadow another skill.

## Goals
- `status` and `apply` refuse an enabled pack that `validate --pack` would fail, naming each file.

## Non-goals
- Re-checking core in `apply` (CI validates core on every PR).
- Changing what `validate` checks (#202 changes model and tool names).

## Acceptance criteria
- **AC1**: Given an enabled pack `acme` with a skill `skills/deploy`, when `apply` runs, then it
  prints ``ERROR acme:skills/deploy: pack skills must start with `acme-` ``, ends with a line
  saying nothing was written and naming `validate --pack <dir>`, exits 1, and creates no link,
  render, or settings change.
- **AC2**: Given the same pack, when `status` runs, then it prints the same `ERROR` line and exits 1.
- **AC3**: Given any other error `validate --pack` reports for that pack's own files (e.g. a skill
  missing `description`), when `apply` runs, then it prints that error and exits 1 the same way.
- **AC4**: Given an enabled pack that passes `validate --pack`, when `apply` runs, then it links
  as before and prints no new lines.

## Constraints
None known.

## Requirement changes

### Area: aicfg-config
#### ADDED: Apply checks packs first
`aicfg status` and `aicfg apply` SHALL run the checks `validate --pack` runs on each enabled
pack's own files, and on any error SHALL print it, write nothing, and exit 1. (AC1, AC2, AC3, AC4)

## Open questions
1. Which checks block `apply`: every error `validate --pack` reports for the pack's files
   (AC3), or only the prefix and pack.toml checks? *Every check is consistent with `doctor`,
   which already FAILs a pack whose `validate --pack` fails, but a pack with one broken doc link
   then can't be applied until it's fixed.* Default: every check (AC3 as written).
