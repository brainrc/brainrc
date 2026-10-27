# Plan: Move CI actions off Node 20 (checkout, setup-python)

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none. These are version bumps of `actions/checkout` and `actions/setup-python`, which both workflows already pin. No new actions are added.
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** CI/CD workflows (security-checklist trigger): T1 gets security-reviewer and infra-reviewer review. Pins stay full-SHA. `permissions`, `GITHUB_TOKEN` use, triggers, and the push steps are unchanged. Checkout v6+ stores persisted credentials in a file under `$RUNNER_TEMP` instead of `.git/config`, and upstream says "no workflow changes required" for `git push`.
- **Domains:** ci-pipelines
- **Environments affected on deploy:** none. After merge, the `release` workflow runs on `main` with the new pins (AC6).
- **Destructive or replacing changes:** none

## Approach
Edit the four existing `uses:` lines in place: two in `.github/workflows/validate.yml` and two in `.github/workflows/release.yml`. Keep the `# vX.Y.Z` comment style. Every `with:` input stays the same. Nothing else changes. Evidence comes from `git ls-remote --tags` and shallow clones taken on 2026-10-27. The release API is blocked in the sandbox, so the dates below are tag commit dates (`git log -1 --format=%cI`).

| Action | Pin | Tag commit date | Age | `action.yml` |
|---|---|---|---|---|
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` | 2026-07-17 | 102 d | `using: node24` |
| `actions/setup-python` | `5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0` | 2026-07-19 | 100 d | `using: 'node24'` |

Choices (AC2/AC3, spec open question 1): v7 is the highest major for both actions, and no v8 tags exist. checkout v7.0.1 is the newest tag and is old enough. The newest setup-python tag is v7.1.0 (`6d4fd22…`, 2026-10-21), which is only 6 days old. So we pin v7.0.0, the newest release at least 14 days old within the latest major. The PR states this. Both SHAs are lightweight-tag commits, and the `v7` major tag resolves to the same commit, so no annotated-tag dereference is needed.

AC4 review, from the upstream changelog and READMEs at those tags:
- **checkout v5 to v7:**
  - v5 moved to node24 and needs runner v2.327.1 or later. GitHub-hosted runners meet that.
  - v6 moved persisted credentials to a separate file. Pushes still work.
  - v7 blocks checking out fork PRs on `pull_request_target` and `workflow_run`. We use neither.
  - v7 also migrated to ESM.
  - `ref` and `fetch-depth` are unchanged in `action.yml` (`fetch-depth: 0` is still "all history"). `persist-credentials` still defaults to `true`.
- **setup-python v6 to v7:** v6 moved to node24, and v7 is an ESM migration with "no changes to action inputs, outputs, or behavior". The `python-version` input is unchanged.
- **Result:** no adjustments needed.

## Files
| File | Change |
|---|---|
| `.github/workflows/validate.yml` | modify: checkout and setup-python pins |
| `.github/workflows/release.yml` | modify: checkout and setup-python pins |
| `changelog.d/220-ci-actions-node24.md` | new: `bump: patch`, one bullet |

## Risks
- The release published date could be later than the tag commit date. With about 100 days of margin, and with v7.1.0 already published after v7.0.0, this is negligible. The PR author confirms the dates on the Releases pages.
- Checkout's credential-file change could break the `release` push. Upstream says no changes are needed, and the post-merge run (AC6) is the check. A failure gets a follow-up fix (spec open question 2).

## Test strategy
No code changes, so there are no unit tests to add.
- **Static checks (offline):** for AC1, grep both workflow files for the four new SHAs, and confirm the old `11d5960`/`a26af69` pins are gone. Run `actionlint` if installed (it is not in this sandbox).
- **AC7:** run `python3 scripts/aicfg.py validate` and `python3 -m unittest discover -s tests`.
- **AC2–AC4:** covered by the evidence above, restated in the PR body.
- **Verify after push:**
  - AC5: the `validate` job is green with no Node 20 deprecation annotation.
  - AC6, after merge: the `release` job is green, with the tag pushed and the release created or "already released".

## Tasks
- [ ] **T1** [agent: implementer] Bump checkout to v7.0.1 and setup-python to v7.0.0 in both workflows, and add the changelog fragment
  - files: `.github/workflows/validate.yml`, `.github/workflows/release.yml`, `changelog.d/220-ci-actions-node24.md`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7
  - evidence: grep the new SHAs and comments, confirm no old SHAs remain, `actionlint` if available, plus the validate and test commands. AC5 and AC6 are recorded as `verify after push: validate` and `verify after merge: release`.
  - review: each (`release.yml` holds `contents: write` and pushes to `main`)
