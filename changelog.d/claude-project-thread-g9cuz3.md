---
bump: patch
---
- Each release now publishes brainrc to PyPI (#108): `release.yml` builds the sdist and wheel from the tag, checks them with `scripts/check_dist.py`, attaches them to the GitHub Release, and uploads them by trusted publishing (OIDC) from a job in GitHub environment `pypi`, with no token. The sdist carries only what the wheel is built from, not `specs/`, `tests/` or `evals/`, and CI builds and checks both files on every PR.
