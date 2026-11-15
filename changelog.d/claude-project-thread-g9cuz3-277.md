---
bump: patch
---
- Homebrew (#277): `brew install brainrc/tap/brainrc` installs a release from the `brainrc/homebrew-tap` tap. After PyPI publishing, `release.yml` writes `Formula/brainrc.rb` with `scripts/homebrew_formula.py` (the URL PyPI lists for the sdist, checked against the sha256 of the file the run built; no resources, since brainrc is stdlib-only, and a caveat to run `brainrc apply --repair` after `brew upgrade`), installs and tests it with Homebrew, and pushes it to the tap over HTTPS with the fine-grained token in secret `HOMEBREW_TAP_TOKEN` (Contents read and write on the tap only), passed to git by a credential helper so it never lands in a URL or the clone's config. Without the secret the step skips with a notice and the release still succeeds.
