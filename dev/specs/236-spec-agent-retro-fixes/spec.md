# Spec: spec-agent fixes from the rename campaign's retros

Ticket: local:specs/tickets/236-spec-agent-retro-fixes.md · Size: small · Status: approved

## Problem
The rename campaign's retros found four process gaps that cost a retry or nearly shipped a bug:
an auto Spec gate approved with a failing living-spec check, a MODIFIED block written as a
one-line summary, a paraphrased rule in a dispatch brief, and a test that only failed on CI
because runners set `XDG_CONFIG_HOME`. A minor bump also nearly released 0.5.0, the version the
deprecation warnings promise removes the old names, before they were removed.

## Goals
- Close each gap with the smallest rule or check that prevents it.

## Non-goals
- Removing the old names (ticket 238).

## Acceptance criteria
- **AC1**: Given `changelog.d/` fragments whose largest bump would release a version at or past `cli.SHIM_REMOVED_IN` while that constant exists, when `validate` (or `release`) runs, then it reports an error naming the version and `SHIM_REMOVED_IN`; a `patch` bump, or no `SHIM_REMOVED_IN`, gives no error.
- **AC2**: Given `TempRepoCase`, then every test runs with `XDG_CONFIG_HOME` unset and restores it afterwards.
- **AC3**: Given spec-agent's SKILL.md, handoff.md and the analyst role, then they say: no auto-approved Spec gate while `living_specs.py check` fails; quote spec/plan rules verbatim in dispatches; MODIFIED blocks hold the full new text.

## Constraints
Stdlib only; skill and role files stay short.

## Requirement changes
### Area: release
#### ADDED: No release reaches the removal version early
`validate` and `release` SHALL refuse fragments whose largest bump would release `SHIM_REMOVED_IN` or later while the deprecated names it governs still exist. (AC1)

## Open questions
None.

## Proposed split
Not applicable.
