Create a GitHub Release for each version tag

## Why
Every merge to `main` gets a `vX.Y.Z` tag but no GitHub Release, so the notes live only inside `CHANGELOG.md`. The repo page shows no "Latest" release, people watching "Releases only" get nothing, and pack authors have no per-version page to link to.

## What changed
- `python3 scripts/aicfg.py release --notes X.Y.Z` prints that version's `CHANGELOG.md` section. An unknown version exits 1. The command is read-only.
- `release.yml` has a new "GitHub Release" step after the tag push:
  - If `gh release view v$VERSION` finds the release, the step skips it.
  - Otherwise it runs `gh release create v$VERSION --verify-tag` with those notes.
  - It runs on every path, so a re-run is a no-op and an existing tag without a release gets one.
  - `GITHUB_TOKEN` is passed through `env:`. No new permissions.
- CONTRIBUTING.md § Releases describes the Release and how to backfill one by hand with **Run workflow**.

## Acceptance criteria
- [x] AC1: prints exactly one version's section, verified by `test_notes_print_one_versions_section`
- [x] AC2: an unknown version exits 1, verified by `test_notes_for_a_missing_version_fail`
- [x] AC3: the workflow creates the Release after the tag push, verified by running the step locally with a stub `gh`
- [x] AC4: an existing release is skipped and the job still succeeds, verified the same way
- [x] AC5: a tag without a release gets one (dispatch or next run), verified the same way on the tag-exists path
- [x] AC6: CONTRIBUTING.md § Releases updated

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py release --notes 0.3.39
```
After merge, the release run publishes the new version as a GitHub Release.

## Follow-ups
- **After merge:** `v0.3.39` stays tag-only. To give it a release: `gh release create v0.3.39 --verify-tag --title v0.3.39 --notes "$(python3 scripts/aicfg.py release --notes 0.3.39)"`.
- LOW: `## 0.3.9-rc` would match `0.3.9`. No such headings exist.
- CI fails on the gitleaks step until #217 merges. That's unrelated to this change.

Spec: `specs/218-github-releases/spec.md` · Plan: `specs/218-github-releases/plan.md`
Closes #218
