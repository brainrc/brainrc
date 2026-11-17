---
bump: patch
---
- Docs site publishing is safer and more exact (#197): the build runs with no write token and a
  separate job pushes `gh-pages`, every build tool is pinned with hashes in
  `.github/docs-requirements.txt`, each release publishes the tag it made, `latest` moves only for
  the newest tag, and links that leave `docs/` point at that tag on GitHub (not inside code).
