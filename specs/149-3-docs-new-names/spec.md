# Spec: Move docs and references to the new skill names

Ticket: local:specs/tickets/149-3-docs-new-names.md (child 3 of 3 of gh:149) · Size: standard · Status: approved

## Problem
149.1 moved `work`, `review`, `plan`, `aws` and `terraform` to `brainrc-*` and kept the old
names as deprecated aliases. The shipped docs, rules, agents and skills still tell users to type
the old names and link the alias stubs, so new users learn names that go away in 0.6.0.

## Goals
- Shipped prose and links use `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws`, `brainrc-terraform` (and `/brainrc-work` etc. as slash commands).
- The release notes say what was renamed, the alias window and the removal release.

## Non-goals
- Code behavior. Tests, evals, sandbox tickets, `specs/` run records and `CHANGELOG.md` keep old names (aliases still work; records are history).
- Removing aliases (0.6.0).

## Acceptance criteria
- **AC1**: Given README.md, CONTRIBUTING.md, docs/, rules/, agents/, skills/ (outside the alias stubs) and examples/sandbox/README.md, when searched for the old names used as a skill or slash command (`/work`, `/review`, `/plan`, `skills/<old>/`, `../<old>/SKILL.md`, "the `<old>` skill"), then none remain, except text that explains the deprecation.
- **AC2**: Given the spec-agent Domains table, when read, then the aws and terraform rows link `../brainrc-aws/SKILL.md` and `../brainrc-terraform/SKILL.md`, and every relative link in changed files resolves.
- **AC3**: Given docs/harness-packages.md (or the install docs), when read, then a short note says the old names are deprecated aliases until 0.6.0, and that a harness which ignores `disable-model-invocation` (Antigravity) may still list them.
- **AC4**: Given README.md, then it stays ≤ 100 lines and `check_tutorial.py --readme` passes.
- **AC5**: Given the changelog fragment, then it lists the five renames, the alias window and the removal release 0.6.0.
- **AC6**: Given `validate`, the unit tests, and both `check_tutorial.py` modes, when run, then all pass. Rule token budgets still hold.

## Constraints
Text edits only; no change to `brainrc/` code or skill behavior. Public repo rules apply.

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
1. Applying the parent delta here: this is the last child, so the `core-skill-names` area lands once, describing fully delivered behavior (149.1 and 149.2 are its base).

## Proposed split
Not applicable.
