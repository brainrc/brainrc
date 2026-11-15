# Campaign gh:275 · one-line install (E26)

## 2026-11-15T00:10:00Z · engine · Campaign gate · one shot
`/brainrc-work --campaign gh:275 --shape ordered`

- Members, in order: #108 (PyPI, epic #95; the epic's "start after"), #276, #277, #278, #279.
  All open, none assigned, none skipped.
- Shape: `ordered` (given; the epic body says ordered). Dependency source: `none`.
- Delivery: `sequential` (the epic body), carried as one draft PR per child against `main`, each
  branch stacked on the previous one (as in E27 and E28). Merge in order, merging `main` into the
  next branch first.
- No dry-run stop: the maintainer asked for the campaign "in a campaign gatework one shot" and for
  each PR to go to review. Per-child Spec and Plan gates are logged here, not stopped on. Merging,
  tagging, releasing and publishing stay with the maintainer.
- Before building, the six issue bodies were updated to the maintainer's 2026-11-14 decisions:
  PyPI pending trusted publisher (environment `pypi`), npm dropped for `npx github:brainrc/brainrc`
  from a root `package.json`, Homebrew in a separate `brainrc/homebrew-tap` pushed with secret
  `HOMEBREW_TAP_DEPLOY_KEY` and skipped cleanly without it.

## engine · gh:108 · Spec and Plan (logged under the Campaign gate)
- Spec: `release.yml` keeps its release job, then a `dist` job builds the sdist and wheel from the
  tag, checks them, attaches them to the GitHub Release (skipping ones already attached), and a
  `pypi` job in environment `pypi` with only `id-token: write` uploads them by trusted publishing
  (`skip-existing`). Workflow-level permissions drop to `contents: read`. The sdist carries only
  what the wheel is built from. CI builds and checks both files on every PR.
- Plan: `.github/workflows/release.yml`, `pyproject.toml` (`[tool.hatch.build.targets.sdist]`),
  `scripts/check_dist.py` (new), a step in `validate.yml`, CONTRIBUTING.md § Releases; tests in
  `tests/test_release_dist.py`.
