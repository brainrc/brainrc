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

## engine · gh:108 · verified
Draft PR #359 (base `main`). `validate` and the full suite passed before the push.

## engine · gh:276 · Spec and Plan (logged under the Campaign gate)
- Spec: the README quickstart is `uvx brainrc status`, `uv tool install brainrc` (or pipx),
  `brainrc apply`, `brainrc status`; needs uv and git. `check_tutorial.py --readme` runs it from
  the temp HOME with `~/.local/bin` first on PATH; `--find-links DIR` sets uv and pip to install
  offline from DIR, so CI tests this checkout's wheel before (and after) PyPI has a release.
  docs/install.md leads with PyPI and keeps git for releases before publishing; `apply` runs from
  the installed command, not uvx (uv's cache can be cleared under the links).
- Plan: README.md, docs/install.md, `scripts/check_tutorial.py`, `validate.yml` (uv 0.13.8, a wheel
  of the checkout); tests in `tests/test_check_tutorial.py` with uv stand-ins.

## engine · gh:276 · verified
Draft PR #360 (base `main`, stacked on #359). `validate` and the full suite passed before the push.

## engine · gh:277 · Spec and Plan (logged under the Campaign gate)
- Spec: `scripts/homebrew_formula.py SDIST` renders `Formula/brainrc.rb`: the sdist from PyPI
  (`--pypi-json` takes the file URL from PyPI's JSON, which the workflow downloads, and refuses a sha256 other than the
  built file's), `depends_on "python@3.13"`, `virtualenv_install_with_resources` with no
  resources, a `brainrc --version` test. `release.yml`'s `homebrew` job runs after `pypi`; with
  no `HOMEBREW_TAP_DEPLOY_KEY` it prints a notice and skips every other step; with it, it
  clones `brainrc/homebrew-tap` over SSH (host keys from `gh api meta`, strict checking), commits
  the formula when it changed, and pushes.
- Plan: `scripts/homebrew_formula.py` (new), `release.yml`, docs/install.md, CONTRIBUTING.md;
  tests in `tests/test_homebrew_formula.py` (render, PyPI JSON read from a file the workflow downloads, `ruby -c`
  where ruby exists, the job's gating).

## engine · gh:277 · verified
Draft PR #361 (base `main`, stacked on #360). `validate` and the full suite passed before the push.
The PyPI lookup moved into the workflow (curl to a JSON file the script reads): scripts make no
network calls (`tests/test_project_files.py`).

## engine · gh:278 · Spec and Plan (logged under the Campaign gate)
- Spec: root `package.json` with `bin: {brainrc: bin/brainrc.js}`, `files: [bin/brainrc.js,
  VERSION]`, `private: true`, no dependencies or scripts, generated with the plugin manifests so
  its version tracks `VERSION` (release commits it; `validate` reports it stale). The shim refuses
  a package.json/VERSION mismatch, runs `uvx brainrc@<VERSION> <args>`, passes the exit code and
  signals, and without uv prints the install link and exits 127. Without a public repo, `npx
  github:` can't fetch it; docs say so.
- Plan: `bin/brainrc.js` (new), `brainrc/plugin.py`, `package.json` (generated), `release.yml`,
  `validate.yml` (npm pack + npx on the packed file, uv offline on the checkout's wheel),
  AGENTS.md, docs/install.md; tests in `tests/test_npx_shim.py`.

## engine · gh:278 · verified
Draft PR #362 (base `main`, stacked on #361). `validate` and the full suite passed before the push.

## engine · gh:279 · Spec and Plan (logged under the Campaign gate)
- Spec: `scripts/check_install_time.py` times each route (uvx, pipx, npx, brew) from the install
  command to the end of the first `status` in a fresh temp HOME; over `--limit` (60 s) is FAIL; a
  missing tool or published source is SKIP. `--local DIST` installs the checkout's build, uv and
  pip offline (pipx uses uv when it can, so both are set), npx from `npm pack`, brew from a scratch
  tap whose formula points at the local sdist by `file://`. `--published` checks PyPI with `pip
  index`, and whether the repo and tap are public with a credential-free `git ls-remote`.
  Homebrew runs without auto-update.
- Workflow `install-time`: matrix ubuntu/macOS × four routes; PRs and pushes `--local`, weekly and
  manual `--published`. Not required, so a slow route is visible without blocking merges.
- Plan: script and workflow (new), docs/install.md; tests in `tests/test_install_time.py`.

## engine · gh:279 · verified
Draft PR #363 (base `main`, stacked on #362). `validate` and the full suite passed before the push.

## review · code-reviewer on each PR (high), confirmed findings fixed
Fixes land on the PR's own branch and reach later branches by merge commits (no rebase).
- #359: pypi-publish pinned to v1.14.3 (Metadata 2.4); build with pinned hatchling, no isolation,
  from the tag with no write token, attach in its own job; `check_dist` matches whole path
  segments and reads force-include from pyproject; re-run wording in CONTRIBUTING.
- #360: the quickstart check drops any `brainrc` already on PATH and uv/pip index settings; the CI
  wheel is built pinned; install.md says how to fix PATH and points to the no-clone route first.
- #361: formula caveat to run `brainrc apply --repair` after `brew upgrade`; the release installs
  and tests the formula with Homebrew before the push; a sha256 mismatch with PyPI isn't retried.
- #362: validate fails when the shim is gone; SIGPIPE exits 141; docs warn that `npx brainrc`
  without `github:` runs an unrelated package and that npx may reuse an old copy.
- #363: helpers loaded by path (no `scripts/` on sys.path); npx needs uv and, published, the
  repo's VERSION on PyPI; an unanswering pip is FAIL; brew keeps its cache, skips when already
  installed and uninstalls after; the workflow runs only on packaging changes.
- Not fixed, for the owner: brainrc isn't on PyPI and `brainrc` isn't reserved on npm; between the
  release's VERSION push and the PyPI upload, `npx github:brainrc/brainrc` pins an unpublished
  version; Homebrew's `python@3.13` needs a bump when Homebrew retires it.

## engine · gh:277 · change: token instead of deploy key (2026-11-15)
The maintainer chose a token over the SSH deploy key. The `homebrew` job now clones and pushes
`brainrc/homebrew-tap` over HTTPS with org secret `HOMEBREW_TAP_TOKEN` (fine-grained, Contents
read and write on the tap only), handed to git by a credential helper that reads it from the
environment, so it never sits in a URL, a command line or the clone's config. Without the secret
it still skips with a notice. This supersedes `HOMEBREW_TAP_DEPLOY_KEY` in the entries above.
