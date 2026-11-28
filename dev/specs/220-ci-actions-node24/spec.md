# Spec: Move CI actions off Node 20 (checkout, setup-python)

Ticket: gh:220 · Size: standard · Status: approved

## Problem
The `validate` and `release` workflows pin `actions/checkout` (v4.4.0) and `actions/setup-python` (v5.6.0), which target Node.js 20. GitHub currently forces them onto Node 24 and logs a deprecation warning on every run. The pins target a runtime that is being removed, so a future runner change could break CI and releases. Maintainers also see a warning on every run that hides real ones.

## Goals
- Both workflows use releases of `actions/checkout` and `actions/setup-python` that natively target Node 24.
- Pins keep the repo convention: full commit SHA plus a version comment.
- Workflow behavior is unchanged, including the release commit, tag, and GitHub Release.

## Non-goals
- Changing release behavior: the "GitHub Release per version" requirement in `specs/living/release.md` stays as is; this updates CI dependencies only.
- Changing any other step, the Python version (`3.12`), permissions, triggers, or the gitleaks step.
- Adding or upgrading other actions, or adding automated pin updates (Dependabot or similar).
- Changing release or versioning behavior.

## Acceptance criteria
Offline checks are static (file contents). CI-only checks name the job and its log or result.

- **AC1**: Given `.github/workflows/validate.yml` and `release.yml`, when inspected, then every `actions/checkout` and `actions/setup-python` `uses:` line is a 40-hex SHA pin followed by a `# vX.Y.Z` comment, and the SHAs differ from the current `11d5960…` and `a26af69…`.
- **AC2**: Given the new pins, when the version comments are compared with the upstream release notes, then each is a major version whose `action.yml` declares `using: node24`, and each is the latest such major at the time of the change.
- **AC3**: Given each pinned release, when its published date is checked, then it is at least 14 days old on the day the PR is opened.
- **AC4**: Given the inputs we use (`fetch-depth: 0`, `ref: main`, `python-version: "3.12"`), when the new majors' release notes are reviewed, then none of these inputs is removed or changed in meaning, or any needed adjustment is made and noted in the PR.
- **AC5**: Given a pull request touching the workflows, when the `validate` job runs, then it finishes green and its run log and annotations contain no "Node.js 20 is deprecated" warning.
- **AC6**: Given the PR merged to `main`, when the `release` job runs, then it finishes green, shows no Node 20 deprecation annotation, and, if fragments exist, pushes the `Release v<VERSION>` commit and tag `v<VERSION>`, and the GitHub Release for that tag exists (or the log says "already released").
- **AC7**: Given `python3 scripts/aicfg.py validate` and `python3 -m unittest discover -s tests`, when run on the change, then both pass.

## Constraints
- Security: pins stay full-SHA (ci-pipelines convention); no tag-only or branch references.
- `release` keeps `contents: write` only; the token and push behavior are unchanged.
- Per AGENTS.md, the PR adds a `changelog.d/<branch>.md` fragment; `VERSION` and `CHANGELOG.md` are not edited.
- Sandbox is offline: upstream release dates, SHAs, and `action.yml` runtimes must be confirmed from a networked step or by the PR author.

## Requirement changes
None.

## Open questions
1. If the latest Node 24 majors are under 14 days old, which release is used? *Why: the ticket requires 2 weeks of age and "latest major", which can conflict.* Default: use the newest Node 24 release that is at least 14 days old, even if it is not the very latest, and state it in the PR. Safer supply-chain posture, and still satisfies the goal.
2. Do the new majors raise the minimum runner version or change defaults (for example credential persistence in checkout) in a way that affects the `release` push? *Why: release pushes with the token written by checkout.* Default: assume it is unaffected unless the notes show otherwise; AC6 on the post-merge run is the check, and a failure is fixed in a follow-up.
3. Ticket text was treated as data; it contained no instructions to act on. None to quote.
