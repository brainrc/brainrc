# Spec: Replace docs/roadmap.md with the epic list

Ticket: gh:203 · Size: small · Status: approved

## Problem
`docs/roadmap.md` still lists three old items and a done list. The plan now lives in the GitHub
epics, so a contributor reading the repo can't see what comes next or in what order.

## Goals
- `docs/roadmap.md` lists every open epic, grouped by wave, with its goal and issue link.
- It says shipped work is in the CHANGELOG.

## Non-goals
- Generating the page from the GitHub API (it would need network in tests and CI).
- Closing finished epics (E2, E22) or editing issues.

## Acceptance criteria
- **AC1**: Given `docs/roadmap.md`, when compared with the open issues titled "Epic …" plus the
  two older roadmap epics their sub-issues name (E17 #63, E18 #18), then every one is listed
  once, with its ID, title, issue link and a one-line goal.
- **AC2**: Given the page, when read, then epics are grouped by wave (the `Roadmap ID` prefix of
  their sub-issues: P0 to P4), with owner decisions, unwaved epics, and epics whose sub-issues
  are all closed in their own groups.
- **AC3**: Given the page, when read, then it links the CHANGELOG for shipped work.
- **AC4**: Given a test, when a roadmap item isn't `- **<ID>** [title](issue link): goal`, an ID
  or issue repeats, or the first item precedes a `## Wave 0` heading, then it fails.

## Constraints
Docs and one stdlib test. No new dependency.

## Requirement changes
None.

## Open questions
None. Defaults taken under `--oneshot`:
1. "Wave" is the `Roadmap ID` prefix (P0–P4) of an epic's sub-issues; no other wave definition
   exists in the repo or the issues.
2. E17 (#63) and E18 (#18) are listed: their sub-issues carry those IDs, though the issues
   aren't titled "Epic".
3. Goals are written fresh (epic bodies hold run instructions, not goals); no sub-issue counts,
   which would go stale.
4. README already links the roadmap from its reference row, so it is unchanged (the E6 stack is
   rewriting it, #259).

## Proposed split
