# Spec: Reject duplicate pack names

Ticket: gh:101 · Size: small · Status: draft

## Problem
A pack's name comes from `name` in its `pack.toml` (else its key in `packs.toml`). Two enabled
packs with the same name share one hooks dir (`<hooks_dir>-<name>`), one label in the rendered
rules, and one set of owned hook entries, so they overwrite each other and `apply` never settles.
Today `validate` passes them (`packs: acme, acme`) and `apply` links both. A pack named `core` is
taken for core itself and fails with unrelated errors.

## Goals
- `validate`, `status`, `apply`, and `doctor` refuse two enabled packs with one name, naming both keys.

## Non-goals
- Disabled packs: their `pack.toml` isn't read, so their name isn't known.
- Two keys pointing at the same directory with distinct names (not a name clash).

## Acceptance criteria
- **AC1**: Given two enabled packs `[one]` and `[two]` whose `pack.toml` both say `name = "acme"`,
  when `validate`, `status`, or `apply` runs, then it prints
  ``ERROR pack name `acme` is used by both [one] and [two]`` and exits 1; `apply` writes nothing.
- **AC2**: Given the same config, when `doctor` runs, then it reports that error as a FAIL, with a
  fix naming `name` in `pack.toml` or `enabled = false`, and exits 1.
- **AC3**: Given an enabled pack `[two]` whose `pack.toml` says `name = "core"`, when `validate` or
  `apply` runs, then it prints ``ERROR pack name `core` is used by both core and [two]`` and exits 1.
- **AC4**: Given one pack whose key differs from its `name` (`[work]`, `name = "acme"`), when
  `validate` runs, then no duplicate error is printed.

## Constraints
None known.

## Requirement changes

### Area: aicfg-config
#### ADDED: Unique pack names
aicfg SHALL refuse, with an error naming both `packs.toml` keys, two enabled packs with the same
name, or a pack named `core`, in `validate`, `status`, `apply`, and `doctor`, and `apply` SHALL
write nothing while it stands. (AC1, AC2, AC3, AC4)

## Open questions
None.
