# Plan: Create a GitHub Release for each version tag

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none (`gh` is preinstalled on GitHub-hosted runners)
- **Public API / contract changes:** new CLI form `aicfg.py release --notes X.Y.Z` (read-only)
- **Migrations / data changes:** none
- **Security triggers touched:** CI/CD workflow that uses `GITHUB_TOKEN` with `contents: write`
  (already granted). T2 gets `review: each` + infra and security review.
- **Domains:** ci-pipelines, scripting
- **Environments affected on deploy:** the next merge to `main` creates a public GitHub Release
- **Destructive or replacing changes:** none (never edits or deletes a release)

## Approach
**Notes command.** `aicfg/release.py` gets `release_notes(text, version) -> str | None`. It finds
`^## <version>\b` with a regex built from `re.escape(version)`, takes the lines after that heading
up to the next `CHANGELOG_VERSION` match (or the end), and strips the result. It returns `None`
when there's no such heading. `cmd_release_notes(version)` reads `config.REPO / "CHANGELOG.md"`
and prints the notes. If the version is missing, it prints
`ERROR CHANGELOG.md has no section for <version>` and returns 1. It's read-only, so it skips
`cmd_release`'s checkout-only guard. `cli.main` routes `release --notes <version>`, and the
usage docstring gains that line.

**Workflow.** A new step in `.github/workflows/release.yml`, after "Commit, tag, and push":
```yaml
- name: GitHub Release
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    version="$(cat VERSION)"
    if gh release view "v${version}" >/dev/null 2>&1; then
      echo "v${version} already released"
    else
      python3 scripts/aicfg.py release --notes "$version" > "$RUNNER_TEMP/notes.md"
      gh release create "v${version}" --verify-tag --title "v${version}" --notes-file "$RUNNER_TEMP/notes.md"
    fi
```
- Every run reaches this step, whether or not it had fragments, so a re-run is skipped (AC4) and
  a tag without a release gets one (AC5).
- No `${{ }}` expression is interpolated into `run:`.
- `--verify-tag` refuses to create the tag if the earlier push somehow didn't happen.

Design choice: read the notes back from `CHANGELOG.md` (Spec gate Q1), so fresh releases, re-runs,
and backfills all take one path.

## Files
| File | Change |
|---|---|
| `aicfg/release.py` | `release_notes`, `cmd_release_notes` |
| `aicfg/cli.py` | route `release --notes <version>`; usage line |
| `tests/test_aicfg.py` | `ReleaseTest`: notes for a middle and the last section, missing version, CLI routing |
| `.github/workflows/release.yml` | GitHub Release step |
| `CONTRIBUTING.md` | § Releases mentions the GitHub Release and the backfill dispatch |

## Risks
- `gh release view` failing for another reason (API down) falls through to `create`, which then
  fails loudly. That's acceptable: the tag is already pushed, and a re-run fixes it.
- The workflow can't be unit tested. The verifier runs the step's shell with a stub `gh` on PATH
  for both branches, plus the real notes command.

## Test strategy
Unit tests in `ReleaseTest` for AC1 and AC2 (via `aicfg.main`). AC3 to AC5: the verifier runs the
step body locally with a stub `gh` that records its arguments, once for a missing release and
once for an existing one. AC6: a doc check.

## Tasks
- [ ] **T1** [agent: implementer] `release --notes <version>` prints a version's changelog section
  - files: `aicfg/release.py`, `aicfg/cli.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2
- [ ] **T2** [agent: implementer] Release workflow creates the GitHub Release; CONTRIBUTING
  - files: `.github/workflows/release.yml`, `CONTRIBUTING.md`
  - criteria: AC3, AC4, AC5, AC6
  - review: each
  - after: T1
