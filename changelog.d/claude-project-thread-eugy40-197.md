---
bump: patch
---
- A docs site built from `docs/` with MkDocs Material (`mkdocs.yml`), with search, a JSON Schemas
  page and one version per minor release. The new `docs` workflow builds it with `--strict` on
  pull requests and, after each release, publishes the release's tag to the `gh-pages` branch
  for GitHub Pages at the default URL (#197).
