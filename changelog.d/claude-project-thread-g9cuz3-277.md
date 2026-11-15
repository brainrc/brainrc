---
bump: patch
---
- Homebrew (#277): `brew install brainrc/tap/brainrc` installs a release from the `brainrc/homebrew-tap` tap. After PyPI publishing, `release.yml` writes `Formula/brainrc.rb` with `scripts/homebrew_formula.py` (the URL PyPI lists for the sdist, checked against the sha256 of the file the run built; no resources, since brainrc is stdlib-only) and pushes it to the tap with the deploy key in secret `HOMEBREW_TAP_DEPLOY_KEY`, checking github.com's host keys against GitHub's API. Without the secret the step skips with a notice and the release still succeeds.
