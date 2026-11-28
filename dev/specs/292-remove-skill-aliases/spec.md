# Spec: remove the deprecated skill aliases

Ticket: gh:292 (review follow-up) · Size: small · Status: approved

## Problem
0.5.14 kept `work`, `review`, `plan`, `aws` and `terraform` as aliases of the `brainrc-` skills
"until 0.6.0". 0.6.0 shipped with them still in place. The owner said to remove them.

## Goals
- The five alias skills and validate's alias check are gone; `review` and `plan` are refused as
  reserved names like any other core skill.

## Non-goals
- The agent aliases, which stay until 0.7.0.

## Acceptance criteria
- **AC1**: Given the shipped tree, then `skills/<old name>` doesn't exist for any of the five, the
  plugin lists only the `brainrc-` names, and validate and the tests pass.
- **AC2**: Given a new core skill named `review` or `plan`, then validate fails naming it as reserved.

## Requirement changes
### Area: core-skill-names
#### REMOVED: Deprecated aliases
Why: their window ended with 0.6.0, so the `brainrc-` names are the only ones from 0.6.1.
#### MODIFIED: Reserved names
`validate` SHALL fail on a core skill that has a reserved built-in name. (AC2)

## Open questions
None.
