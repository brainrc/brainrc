# Spec: Reserved skill names check in validate

Ticket: local:specs/tickets/149-2-reserved-names.md (child 2 of 3 of gh:149) · Size: small · Status: approved

## Problem
Nothing stops a new core skill from taking a name that shadows a harness built-in. 149.1 moved
the five colliding skills to `brainrc-*`; this child keeps it that way.

## Goals
- `validate` rejects a core skill whose name is reserved, unless it is a declared deprecated alias.

## Non-goals
- Checking pack skill names (packs already carry a prefix) or agents.
- Verifying the reserved list against each harness (no built-in list exists in the repo).

## Acceptance criteria
- **AC1**: Given a core skill named `init`, `help`, `status`, `compact`, `review` or `plan` that is not in `DEPRECATED_ALIASES`, when `validate` runs, then it exits 1 and the error names the skill dir and the reserved name.
- **AC2**: Given the shipped repo (where `review` and `plan` are declared deprecated aliases), when `validate` runs, then it passes; and a pack skill named `status` is not rejected by this check.
- **AC3**: Given the existing "defined in both" duplicate check, when a pack and core define the same skill, then that error still fires, unchanged.

## Constraints
Stdlib only. A patch changelog fragment.

## Requirement changes
None.

## Open questions
1. Reserved list. Default (parent Q1): `review`, `plan`, `init`, `help`, `status`, `compact`, kept as one constant so it is easy to extend.

## Proposed split
Not applicable (small).
