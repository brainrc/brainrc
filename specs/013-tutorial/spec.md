# Spec: Tutorial for your first domain skill and your first pack

Ticket: gh:13 · Size: standard · Status: draft

## Problem
`docs/formats.md` shows the file formats and `docs/packs.md` the pack reference, but nothing
walks a newcomer from an empty directory to a working extension that `aicfg` installs and
spec-agent picks up. They have to assemble the steps from four docs and the example pack.

## Goals
- One tutorial (Divio type: tutorial) a newcomer follows top to bottom and ends with a working,
  validated extension installed into their AI tool.

## Non-goals
- Reference material (stays in `formats.md`, `packs.md`, `connectors.md`).
- Contribution process for core (#15, CONTRIBUTING.md).
- Proving a model actually loads the skill in a live session (that is #6, evals).

## Acceptance criteria
- **AC1**: `docs/tutorial.md` takes the reader from a fresh clone of core to a pack of their own
  with one domain skill (Validate / Conventions / Review checklist / Never without approval),
  registered through `[[extensions.domains]]`, enabled in `packs.local.toml`, applied with
  `status` then `apply`, and checked with `validate --pack` and `aicfg tokens`.
- **AC2**: Every step shows the exact command and what the reader should see afterwards.
- **AC3**: It ends with how to validate the pack in its own CI, and a short "contributing a
  domain skill to core instead" section that points to the Domains table and CONTRIBUTING.
- **AC4**: A script in `specs/013-tutorial/` runs every command in the tutorial on a fresh clone
  with a temporary HOME, and all pass. The run is recorded in `verify.md`.
- **AC5**: README "Adding content" links the tutorial. `VERSION` 0.3.3, CHANGELOG entry,
  `validate` and tests pass.

## Constraints
Generic content only (example stack and pack names). Prose follows the unslop rules. Keep it
under ~150 lines.

## Open questions
1. **Build the domain skill inside the pack, not core?** Default: yes. Most readers extend
   ai-config for themselves, and a pack needs no change to core. The issue's core path becomes
   the short closing section. *Matters because* it decides the tutorial's whole path.
2. **Example stack?** Default: Protocol Buffers (`*.proto`, validated with `buf lint`). It's
   generic, has no core skill yet, and its checks are offline.
3. **"See it load" in a sandbox ticket?** Default: show where spec-agent lists it (the
   rendered `extensions.md` Domains table) instead of a live model run, which this tutorial
   can't verify.
