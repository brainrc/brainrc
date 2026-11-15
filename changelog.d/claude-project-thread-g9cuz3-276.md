---
bump: patch
---
- The README quickstart installs from PyPI (#276): `uvx brainrc status` to preview, then `uv tool install brainrc` (or `pipx install brainrc`), `brainrc apply` and `brainrc status`. No clone or Python of your own needed; uv fetches one. docs/install.md leads with the PyPI routes and keeps the git URL for releases before PyPI publishing. `check_tutorial.py --readme` runs the quickstart from the temp HOME with `~/.local/bin` on PATH and no other `brainrc` there, drops uv and pip index settings, and `--find-links DIR` makes uv and pip install brainrc offline from a wheel in DIR, which CI builds from the checkout.
