# Spec: Create a GitHub Release for each version tag

Ticket: gh:218 · Size: standard · Status: approved

## Problem
Every merge to `main` gets a `vX.Y.Z` tag from `release.yml`, but no GitHub Release. The
release notes exist only inside `CHANGELOG.md`. The repo page shows no "Latest" release, people
watching "Releases only" get no notification, and pack authors pinning `requires_core` have no
per-version page to link to.

## Goals
- Every version tag the release workflow pushes gets a GitHub Release whose body is that
  version's `CHANGELOG.md` section.
- Re-running the workflow never duplicates a release or fails because one exists.
- The current tag (`v0.3.39`) can get its release without a new version.

## Non-goals
- Attaching wheel or sdist files.
- Releases for tags older than the current `VERSION`.
- Replacing `docs/install.md`'s old `bxker/ai-config` URLs (separate fix).
- Changing how versions, tags, or fragments work.

## Acceptance criteria
- **AC1**: Given `CHANGELOG.md` has a `## X.Y.Z (date)` section, when the release-notes command
  runs for `X.Y.Z`, then it prints exactly that section's body: the lines after the heading, up to
  the next `## ` version heading, with no surrounding blank lines.
- **AC2**: Given no section exists for the version asked for, when the command runs, then it
  exits non-zero with an error naming the version, and prints no notes.
- **AC3**: Given a merge with fragments, when `release.yml` runs, then after pushing the tag it
  creates a GitHub Release titled `vX.Y.Z` for that tag, with the AC1 notes as its body.
- **AC4**: Given the release for `vX.Y.Z` already exists (a re-run, or the no-fragments path for a
  tag that's already there), when `release.yml` runs, then it creates nothing new and the job
  still succeeds.
- **AC5**: Given the tag `vX.Y.Z` exists with no release (today's `v0.3.39`), when the workflow
  is run by hand (`workflow_dispatch`) or on the next push with no fragments, then the release is
  created for the current `VERSION`.
- **AC6**: Given CONTRIBUTING.md § Releases, when a contributor reads it, then it says each
  release tag also gets a GitHub Release with the changelog notes.

## Constraints
- Stdlib only for `aicfg`. The workflow uses `gh` (preinstalled on runners) with the job's
  `GITHUB_TOKEN`; `contents: write` is already granted; no new secrets or permissions.
- CI/CD workflow change (security trigger): no `${{ }}` expressions interpolated into `run:`.
- PR CI stays red on the gitleaks step until #217 merges; that is not this change's failure.

## Requirement changes

### Area: release
Purpose: How a merge to `main` becomes a version, a tag, and a GitHub Release.
#### ADDED: GitHub Release per version
The release workflow SHALL create a GitHub Release for each `vX.Y.Z` tag it pushes or finds
without one, with that version's `CHANGELOG.md` section as the body, and SHALL NOT create a
duplicate when the release exists. (AC1, AC2, AC3, AC4, AC5)

## Open questions
None. Resolved at the Spec gate: Q1 one command reads a version's section from `CHANGELOG.md`.
