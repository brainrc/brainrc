Move CI checkout and setup-python off Node 20

## Why
The `validate` and `release` workflows pinned `actions/checkout` v4.4.0 and `actions/setup-python` v5.6.0. Both run on Node 20, and GitHub now forces them onto Node 24 with a deprecation warning on every run. The warning hides real ones, and a runner change could break CI and releases.

## What changed
- `validate.yml` and `release.yml` now pin `actions/checkout` v7.0.1 (`3d3c42e…`) and `actions/setup-python` v7.0.0 (`5fda3b95…`). Both are full-SHA pins with a version comment, as before. Both `action.yml` files declare Node 24.
- Inputs are unchanged: `fetch-depth: 0`, `ref: main`, `python-version: "3.12"`. Checkout still persists credentials by default. The release push path is unchanged.
- setup-python stays at v7.0.0, not v7.1.0 (see Decisions).
- Adds the `changelog.d/220-ci-actions-node24.md` fragment (`bump: patch`).

Blast radius: the two workflow files only. Nothing is destroyed or recreated. The `release` job runs on `main` with the new pins after merge, and it holds `contents: write`.

## Acceptance criteria
- [x] AC1: every checkout and setup-python `uses:` line is a 40-hex SHA with a `# vX.Y.Z` comment, and the old SHAs are gone, verified by `grep -n 'uses:'` on both files
- [x] AC2: both pinned tags are the latest major (v7), and both `action.yml` files declare Node 24, verified by shallow clones at the tags; no v8 tags exist
- [x] AC3: pinned tags are at least 14 days old, verified by tag commit dates (checkout 2026-07-17, setup-python 2026-07-19). Release publish dates were not checked (see Follow-ups)
- [x] AC4: no input we use changed meaning in v5 to v7, verified against `action.yml` and the release notes at each tag
- [ ] AC5: `validate` is green with no "Node.js 20 is deprecated" annotation. Checked on this PR's run
- [ ] AC6: `release` is green on the first post-merge run, and the `Release v<VERSION>` commit, tag, and GitHub Release exist (or the log says "already released"). Checked after merge
- [x] AC7: `python3 -m unittest discover -s tests` and `python3 scripts/aicfg.py validate` both pass (438 tests)

## How to verify
```
grep -n 'uses:' .github/workflows/validate.yml .github/workflows/release.yml
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```
After push: the `validate` job log has no Node 20 deprecation warning.
After merge: the `release` job log has no Node 20 warning, and the tag and release exist.

## Decisions made without you
- Gates auto-approved: Spec, Plan (Deliver is auto-approved after the drafts); see `specs/220-ci-actions-node24/log.md`
- Open question 1 (latest Node 24 release is under 14 days old): setup-python v7.1.0 was tagged 2026-10-21, which is 6 days old. Pinned the newest v7 release at least 14 days old, v7.0.0.
- Open question 2 (does checkout v7 change the release push): assumed no. Upstream says no workflow change is needed, and checkout v6+ stores persisted credentials in a file under `$RUNNER_TEMP`. AC6 on the first post-merge release run is the check. Rollback: revert the checkout pin to v4.4.0 `11d5960a326750d5838078e36cf38b85af677262`.
- Security trigger touched without a CRITICAL/HIGH finding: CI/CD workflows. Security, infra, and code review found none.
- Ticket comment not posted: `specs/220-ci-actions-node24/ticket-comment.md`

## Follow-ups
- LOW: the release push is only proven by the first post-merge `release` run (AC6). Rollback is above.
- LOW: AC3 uses tag commit dates as a proxy because the GitHub release API was blocked in the sandbox. The margin is about 100 days.
- `actionlint` and `zizmor` were not run because neither is installed. The YAML was checked by inspection.

Spec: `specs/220-ci-actions-node24/spec.md` · Plan: `specs/220-ci-actions-node24/plan.md`
Closes #220
