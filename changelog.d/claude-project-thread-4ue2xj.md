---
bump: patch
---
- Docs: the spec for a project's `brainrc.toml` and its `brainrc.lock` (#281), in
  [docs/project.md](docs/project.md), with JSON Schemas for both in `docs/schemas/` and
  conformance fixtures in `tests/fixtures/lockfile/`. `brainrc/schema.py` checks a file against a
  schema with the standard library alone. Nothing reads or writes either file yet.
