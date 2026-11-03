# Spec: Open-source project files

Ticket: gh:146 (campaign gh:113, child 1 of 4) · Size: standard · Status: approved

## Problem
The repo is public but lacks most files GitHub's community profile checks: no code of conduct,
security policy, issue or PR templates, and no stated ownership, governance, or data-handling
position. A reader cannot tell how to report a guard bypass privately, how decisions are made,
or whether the tooling phones home. Only README, LICENSE, and CONTRIBUTING exist today.

## Goals
- Every checklist item the repo can satisfy by a PR is present: CODE_OF_CONDUCT, SECURITY,
  issue templates, PR template (README, LICENSE, CONTRIBUTING already exist).
- Add CODEOWNERS, GOVERNANCE, and a no-telemetry statement, all discoverable from README.

## Non-goals
- The repository description (a repo setting). Follow-up for the owner, not part of the PR.
- Enabling GitHub private vulnerability reporting (a repo setting). Follow-up, see Q1.
- Changing hooks, guard patterns, runtime code, or adding any dependency.
- Contributor-license agreements, funding files, or Discussions.

## Acceptance criteria
- **AC1**: Given the repo root, when listed, then `CODE_OF_CONDUCT.md`, `SECURITY.md`, and
  `GOVERNANCE.md` exist, and `.github/` holds `CODEOWNERS`, a PR template, and issue templates.
- **AC2**: Given `SECURITY.md`, when read, then it summarizes the guard model (hooks are a
  seatbelt, credentials are the real boundary) and links `docs/guardrails.md`, says what counts
  as a guard bypass worth reporting versus a documented known gap, and says to report privately
  through GitHub's "Report a vulnerability" (Security tab), not in public issues.
- **AC3**: Given `SECURITY.md`, when read, then it gives the supported version policy and an
  expected-response statement that makes no unkeepable time promise.
- **AC4**: Given `CODE_OF_CONDUCT.md`, when read, then it is the Contributor Covenant (current
  2.x text, attributed) and names the private reporting channel from Q1, not a personal email.
- **AC5**: Given `.github/CODEOWNERS`, when parsed, then every pattern is valid and `bxker` is
  the owner for all paths (`*`).
- **AC6**: Given the issue templates, when read, then a bug-report and a feature-request form
  exist, and a `config.yml` points security reports to the private channel, not an issue.
- **AC7**: Given the PR template, when read, then it asks why, what changed, how to verify, and
  `Closes #N`, and reminds about the changelog fragment and the two check commands (as in CONTRIBUTING).
- **AC8**: Given `GOVERNANCE.md`, when read, then it states who decides (maintainer), how changes
  are accepted (PR, squash-merge, CI green), and how a contributor becomes a maintainer.
- **AC9**: Given the no-telemetry statement, when read, then it says brainrc sends no usage data,
  and notes the only external command is the optional, opt-in `ccusage` (`--ccusage`) run locally.
  The claim holds against the code at merge.
- **AC10**: Given README, when read, then it links each new file, and the existing Security
  section points to `SECURITY.md`.
- **AC11**: Given any added file, when scanned, then it has no personal email, internal hostname,
  employer name, or absolute home path, and `validate` and the unit tests pass.
- **AC12**: Given the PR, when checked, then it adds one `changelog.d/<branch>.md` fragment.

## Constraints
- Public repo rules in AGENTS.md apply. No runtime dependency. Keep files short.
- Do not edit generated files (`dist/`, plugin manifests) or `VERSION`/`CHANGELOG.md`.
- Offline only: the community profile percentage cannot be verified in the run; verify by
  checklist against AC1.

## Requirement changes
None.

## Open questions
1. Private contact for security and conduct reports, *no email may be committed*. Safe default:
   GitHub private vulnerability reporting for both; docs say so. The owner must enable it in
   repo settings (follow-up), or the link dead-ends. Conduct reports may use a maintainer-contact
   line pointing to the same channel.
2. Is "100%" achievable from a PR alone, *the ticket's done-when is the profile score*. Default:
   the PR delivers all file-based items; the description and settings are follow-ups listed in the PR body.
3. Supported versions, *SECURITY needs a policy*. Default: only the latest release is supported.
4. Issue-template format, *forms vs markdown*. Default: YAML issue forms, blank issues disabled.

## Proposed split
Not applicable (standard).
