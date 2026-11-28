# Verify: Move CI actions off Node 20 (checkout, setup-python)

Run at 2026-10-27T04:14Z on commit `ef9095c` (implementation commit `d0f63e3`; the diff under review is `git diff main...HEAD -- . ':!specs'`, clean working tree).

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (log: `specs/220-ci-actions-node24/.runs/test.log`) | pass: Ran 438 tests, OK (0 failed), exit 0 |
| Lint | none configured (`lint: null`); actionlint, zizmor, shellcheck, yamllint not installed | not configured |
| Build | none configured (`build: null`) | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` (log: `.runs/validate.log`) | pass: `OK: 26 skills, 9 agents, 0 commands`, exit 0 |
| Validate (pack, as CI runs it) | `python3 scripts/aicfg.py validate --pack examples/pack-acme` (log: `.runs/validate-pack-acme.log`) | pass: `OK: 28 skills, 9 agents, 1 commands (packs: acme)`, exit 0 |
| Upstream tags | `git ls-remote https://github.com/actions/checkout 'refs/tags/v7*' 'refs/tags/v8*'` and same for `actions/setup-python` (log: `.runs/upstream.log`) | no v8 tags in either repo |
| Plan / diff | not applicable (no infra) | offline only |

No test in `tests/` references the workflow files, so AC1 to AC4 are verified by the manual checks below, not by unit tests.

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `grep -n 'uses:' .github/workflows/validate.yml .github/workflows/release.yml` returns exactly four lines: `validate.yml:16` `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`; `validate.yml:19` `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0`; `release.yml:26` and `release.yml:30` with the same two SHAs and comments. All SHAs are 40-hex and differ from `11d5960…` and `a26af69…`. | pass |
| AC2 | Shallow clones of tags (`git clone --depth 1 --branch <tag>`): checkout `v7.0.1` → `3d3c42e5…`, `action.yml` line 116 `using: node24`; setup-python `v7.0.0` → `5fda3b95…`, `action.yml` line 42 `using: 'node24'`. Both tags match the SHAs in the workflows. `ls-remote` shows no v8 tags. Checkout's latest major is v7 (tags v7.0.0, v7.0.1). Setup-python's latest major is v7, but v7.1.0 (`6d4fd22b…`) exists and was tagged 2026-10-21 (6 days old), so it is excluded by AC3 and by Open Question 1. v7.0.0 is the newest v7 release at least 14 days old. | pass |
| AC3 | Commit dates of the pinned tagged commits: checkout v7.0.1 `2026-07-17T14:45:11-04:00`; setup-python v7.0.0 `2026-07-19T22:02:03-05:00`. Both are more than 14 days before 2026-10-27. Caveat: GitHub release publish dates were not read, since that is outside the allowed read-only set. A release published after 2026-10-13 on an older commit is not ruled out by this evidence. | pass (commit-date proxy) |
| AC4 | `action.yml` at the pinned tags declares `ref`, `fetch-depth` (default 1; workflows set 0), and `persist-credentials` (default true) for checkout; `python-version` for setup-python (v7.0.0 line 6, description unchanged in meaning). Checkout v7.0.0 and v7.0.1 notes: fork PR refusal applies only to `pull_request_target`/`workflow_run`, not to the `validate` (`pull_request`) or `release` (`push`) triggers. Credentials are still persisted by default; the storage location moved to a file under `$RUNNER_TEMP`. No input we use was removed or changed in meaning. The push path is covered by AC6 post-merge. | pass |
| AC5 | Requires a PR run of the `validate` job. | verify after push: validate |
| AC6 | Requires the post-merge `release` run. | verify after merge: release |
| AC7 | `python3 -m unittest discover -s tests` → `Ran 438 tests … OK`, exit 0. `python3 scripts/aicfg.py validate` → exit 0. | pass |

## Notes
- Changelog fragment `changelog.d/220-ci-actions-node24.md` is present with `bump: patch`; `VERSION` and `CHANGELOG.md` are unchanged. `validate` passed with the fragment present.
- Open Question 1 decision, for the PR description: setup-python is pinned to v7.0.0, not the newer v7.1.0, because v7.1.0 is under 14 days old. The changelog fragment does not mention this. The PR description should state it (AC4 and Open Question 1 both ask for it).
- Open Question 2 (`release` push after checkout v7): credentials are still persisted by default. Confirmed by AC6 on the post-merge run only.
- Offline limits: no actionlint or zizmor run, since neither is installed. Workflow YAML was checked by inspection only.
- No flaky tests observed. Each command was run once.
