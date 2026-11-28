# Spec: document the pack naming rules

Ticket: gh:293 · Size: standard · Status: approved

## Problem
A pack author has no written rule for what a pack may be called, so nothing stops a pack that
looks official, borrows a vendor's name or squats one letter away from `brainrc`.

## Goals
- `docs/packs.md` states the seven rules from the owner's brief, and the official pack ID table.

## Non-goals
- Enforcing them (gh:294). Renaming core agents (gh:295). The pack index and signing (#187, #319).

## Acceptance criteria
- **AC1**: Given `docs/packs.md`, then a `## Naming` section lists exactly seven rules: `brainrc-` and
  `brainrc/` reserved for official packs; a registry prefix starts with the owner's handle; no vendor
  names without verification; no names one or two edits from an official name; ASCII lowercase,
  digits and hyphens only; a prefix is 2 to 24 characters; item names are prefix-scoped.
- **AC2**: Given the same section, then a table lists the official pack IDs: `brainrc/starter`,
  `brainrc/review`, `brainrc/go`, `brainrc/terraform-aws`, `brainrc/kubernetes`, `brainrc/security-baseline`.

## Requirement changes
None (docs only; the enforced behavior is gh:294's).

## Open questions
None. Defaults taken under the auto run:
1. The roadmap table isn't in this repo; the IDs come from the open "Official pack" issues.
2. "2 to 24 characters" counts the prefix without its trailing hyphen, so `go-` is the shortest.
