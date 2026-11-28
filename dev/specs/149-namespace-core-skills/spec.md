# Spec: Namespace core skills

Ticket: gh:149 · Size: large · Status: approved

## Problem
Core ships skills named `work`, `review`, `plan`, `aws` and `terraform`. On installs where
`brainrc apply` links skills into a harness skills dir, these bare names can shadow a harness
built-in slash command or a user's own skill of the same name. (Plugin installs already show
`brainrc:<name>`, so they are less exposed.) Users type and pin these names, so any change is a
public contract change. The repo holds no list of built-in names; which names truly collide is
unverified (see Open questions 1).

## Goals
- Core skills that collide get a namespaced name under a core prefix.
- Old names keep working for one minor release, with a deprecation note, then go.
- A check stops a new core skill from taking a reserved (built-in) name.

## Non-goals
- Removing any old name in this change.
- Renaming the `spec-*`, `ticket-*`, `commit-message` and other domain skills, or agents and commands.
- Changing pack prefix rules, or what the skills do.
- Auto-migrating users' pinned references or their own skills.

## Acceptance criteria
- **AC1**: Given a fresh `brainrc apply` of core, when skills are linked, then `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws` and `brainrc-terraform` exist and behave as the old skills did.
- **AC2**: Given the old names `work`, `review`, `plan`, `aws`, `terraform`, when invoked, then each still performs the same task and says it is deprecated, names its replacement and the release that removes it.
- **AC3**: Given the model chooses skills by description, when both an old and a new name exist, then only one of the pair can be auto-selected (the alias never doubles a trigger).
- **AC4**: Given a core skill whose name is on the reserved list and is not a declared deprecated alias, when `validate` runs, then it fails naming the skill and the reserved entry.
- **AC5**: Given the five old names declared as deprecated aliases, when `validate` runs on the shipped repo, then it passes.
- **AC6**: Given a core skill name that is also a pack's skill name, when `validate` or `apply` runs, then the existing "defined in both" error still fires (unchanged).
- **AC7**: Given any skill that names another core skill (e.g. the spec-agent Domains table, a pack's `domains` entry), when `validate` runs, then both old and new names resolve, and the shipped docs use the new names.
- **AC8**: Given a plugin build, when generated, then it carries the new and alias skills and `validate` fails on a stale manifest.
- **AC9**: Given the release, when its changelog fragment is read, then it lists the five renames, the alias window and the removal release.

## Constraints
- Old names must not be removed in this release (oneshot default: unchanged or additive).
- Core stays stdlib-only; no new dependencies.
- Packs may reference core skill names (docs/packs.md); packs pinning `requires_core` must keep working through the window.
- Per CHANGELOG policy a breaking pack-contract change bumps MINOR while 0.x; additive plus deprecation is stated in the fragment.

## Requirement changes
### Area: core-skill-names
Purpose: Core skill names are namespaced, never shadow reserved names, and old names get a deprecation window.
#### ADDED: Namespaced core skills
The system SHALL ship `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws` and `brainrc-terraform`. (AC1, AC7, AC8)
#### ADDED: Deprecated aliases
The system SHALL keep `work`, `review`, `plan`, `aws` and `terraform` working through one minor release, each printing a deprecation note, and SHALL NOT let an alias double an auto-trigger. (AC2, AC3, AC5)
#### ADDED: Reserved names
`validate` SHALL fail on a core skill that has a reserved built-in name and is not a declared deprecated alias. (AC4, AC6)

## Open questions
1. Which names really collide? No built-in list is in the repo. Believed (unverified): `review` and `plan` match Claude Code built-ins; `work`, `aws`, `terraform` collide only with user skills. *Matters: the reserved list and the headline claim.* Safe default: reserve `review`, `plan`, `init`, `help`, `status`, `compact`, and rename all five regardless.
2. Prefix choice. Default `brainrc-` (matches pack-prefix style) though the plugin form reads `brainrc:brainrc-work`. *Matters: the name users will pin for years.*
3. Do alias names stay shadowing built-ins during the window? Default yes, exempt in `validate` and removed at the stated release. *Matters: "no core skill shadows a built-in" is only true after removal.*
4. Removal release: default the next minor after this one. *Matters: sets the deprecation text and the release gate.*
5. Size. Roughly 80 files mention these names (docs, 40 eval cases, agents, tests). Argued `large`.

## Proposed split
1. **Add namespaced skills and aliases**: AC1, AC2, AC3, AC8.
2. **Reserved-name check in validate**: AC4, AC5, AC6.
3. **Move docs, references and Domains table to new names, changelog fragment**: AC7, AC9. Evals may keep old names during the window.
