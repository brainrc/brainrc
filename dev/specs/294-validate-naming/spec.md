# Spec: validate enforces the pack naming rules

Ticket: gh:294 · Size: standard · Status: approved

## Problem
The rules in docs/packs.md § Naming (gh:293) aren't checked, so they drift the first time someone
publishes a pack.

## Goals
- `validate` (and `apply`, which runs the same pack checks) refuses a pack that breaks a rule.
- A pack can declare the ID it's published under, so rules 1 to 4 have an owner to check against.

## Non-goals
- Proving who owns an ID (signing, #319) or running the verified vendor program (#333).

## Acceptance criteria
- **AC1**: Given a pack that isn't official, when its name, prefix or `id` starts with `brainrc-` or
  `brainrc/` (or is `brainrc`), then validate fails; `acme-brainrc-` passes, and so does an official ID.
- **AC2**: Given `id = "<owner>/<pack>"`, when the prefix doesn't start with `<owner>-`, then validate fails;
  `<owner>-` and `<owner>-<more>-` pass. A malformed `id` fails.
- **AC3**: Given a name, prefix or ID with a vendor name as a word (`aws-tools`), then validate fails;
  `awsome` passes, and a verified owner may use its own vendor name.
- **AC4**: Given a name, prefix, owner or first word one or two edits from `brainrc`, or an ID one or two
  edits from an official ID, then validate fails; three edits (`bran`) pass.
- **AC5**: Given a non-ASCII or uppercase name, prefix, agent, command or MCP server name, then validate
  fails; digits pass.
- **AC6**: Given a prefix under 2 or over 24 characters before its hyphen, then validate fails.
- **AC7**: core, `examples/pack-acme` and `examples/pack-homelab` still pass, and the docs' ID table
  matches validate's list.

## Requirement changes
### Area: validate
#### ADDED: Pack naming rules
`brainrc validate` SHALL refuse a pack whose names break docs/packs.md § Naming, and `apply` SHALL
refuse to link it. (AC1 to AC7)

## Open questions
None. Defaults taken under the auto run:
1. The pack ID is a new optional `pack.toml` key, `id = "<owner>/<pack>"`. Without it, rule 2 has no
   owner and only the other rules apply. A pack is official when its `id` is in the table.
2. "Starts with the owner's handle" means `<owner>-`, so owner `jdoe` can't take `jdoex-`.
3. Rule 4 compares the whole name and its first word, so `brainrx-tools` is caught. A swap of two
   neighbours counts as one edit.
4. The vendor list is 20 company and AI-product names, kept in `brainrc/naming.py`.
