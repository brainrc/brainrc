# Spec: Fix doc drift

Ticket: gh:105 · Size: small · Status: approved

## Problem
Docs drifted from the code. The install guide tells people to stay on `v0.3.29`, two releases
of breaking renames ago. `overrides/README.md` says only Claude Code is synced, though Cursor's
hooks and OpenCode's guard plugin are too. AGENTS.md states the repo is public while it is still
private (going public is the owner's step from #107). `brainrc doctor` prints `rm` fixes with
unquoted paths, so a path with a space breaks or deletes the wrong thing when pasted.

## Goals
- No stale release pin in the install docs, and a test that keeps it that way.
- `overrides/README.md` matches what `apply` syncs.
- Doctor's `rm` fixes are safe to paste.

## Non-goals
- Historical version mentions ("removed in 0.5.0", CHANGELOG, e2e run notes, run records).
- Rewriting the README (E6, #148) or the roadmap (#203).

## Acceptance criteria
- **AC1**: Given `docs/install.md`, when read, then it pins no concrete release; staying on a
  release reads `git checkout v<X.Y.Z>` with a link to Releases.
- **AC2**: Given the install docs (README, CONTRIBUTING, install, tutorial, troubleshooting),
  when a test scans them, then any release pin (`git checkout vX.Y.Z`, `@vX.Y.Z`, `brainrc==X.Y.Z`,
  `--branch vX.Y.Z`) must match `VERSION`'s major.minor, else the test fails naming the line.
- **AC3**: Given `overrides/README.md`, when read, then it says Claude Code and Cursor hooks and
  settings fragments, and OpenCode's plugin, are synced, and Codex and Antigravity have none.
- **AC4**: Given AGENTS.md and the README, when read, then they say to treat the repo as public,
  which holds before and after the owner flips it.
- **AC5**: Given a doctor finding whose fix is `rm <path>` or `rm -r <path>`, when the path has
  a space, quote or shell metacharacter, then the printed path is shell-quoted with `~` left
  unquoted, and the shell reads it back as the same path; plain paths print as before.

## Constraints
Stdlib only (`shlex`). No new dependency.

## Requirement changes
### Area: doctor
Purpose: What `brainrc doctor` reports and the fixes it prints.
#### ADDED: Pasteable rm fixes
`brainrc doctor` SHALL print each `rm` fix's path shell-quoted, with a leading `~` left outside
the quotes, so the command removes exactly that path when pasted. (AC5)

## Open questions
None. Defaults taken under `--oneshot`:
1. AGENTS.md says "treat this repo as public" rather than "private": the repo is private today
   but going public is decided (#107), and the rule it carries is the same either way.
2. "Docs reference the current major.minor" is read as: release pins in install docs match it,
   and a placeholder is preferred, so the docs don't need an edit on every release.
3. Doctor's file reference (`doctor.py:118`) moved; all three `rm` fixes are covered.

## Proposed split
