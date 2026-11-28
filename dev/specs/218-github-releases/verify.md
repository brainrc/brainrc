# Verify: Create a GitHub Release for each version tag

Run at 2026-10-26T03:37:04Z on commit `db7effe`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 369 passed, 0 failed |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK: 26 skills, 9 agents, 0 commands |
| Plan / diff | release.yml step run locally under `bash -e` with a stub `gh` | pass: both branches (see AC3, AC4) / offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `tests.test_aicfg.ReleaseTest.test_notes_print_one_versions_section` passes (a middle and the last section, exact output); manual: `python3 scripts/aicfg.py release --notes 0.3.39` prints the 0.3.39 section | pass |
| AC2 | `test_notes_for_a_missing_version_fail` passes (`0.3.1` isn't a prefix match for `0.3.10`); manual: `release --notes 9.9.9` → `ERROR CHANGELOG.md has no section for 9.9.9`, exit 1 | pass |
| AC3 | manual: the step body with a stub `gh` and no release → `gh release view v0.3.39`, then `gh release create v0.3.39 --verify-tag --title v0.3.39 --notes-file …`; the notes file equals the `release --notes 0.3.39` output (empty diff); exit 0 | pass |
| AC4 | manual: same with the release already present → only `gh release view`, prints "v0.3.39 already released", exit 0 | pass |
| AC5 | manual: the AC3 run was for the current VERSION with its tag already present (the no-fragments path that `workflow_dispatch` takes); the step runs on every path, after the tag step | pass |
| AC6 | manual: CONTRIBUTING.md § Releases says each tag gets a GitHub Release with its CHANGELOG section, and how to backfill one by hand | pass |

## Notes
- The workflow can't run offline. AC3 to AC5 were checked by running the step's own `run:` body (taken from release.yml) against a stub `gh`. The first real evidence will be the release run after this PR merges.
- That merge publishes `v0.3.40` (or whatever the next version is) as a public GitHub Release. `v0.3.39` stays tag-only unless the workflow is run by hand before that merge, or someone runs `gh release create v0.3.39` with its notes.
- PR CI fails on the gitleaks step until #217 merges. That's unrelated to this change.
