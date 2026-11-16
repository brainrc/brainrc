---
bump: patch
---
- **[pack contract]** JSON Schemas for `pack.toml`, `mcp/servers.toml` and `harnesses.toml` in
  `docs/schemas/`, with `.taplo.toml` and a `#:schema` first line (written by `brainrc import`) for
  editor completion. `validate` checks a pack's `pack.toml` against its schema: a known key of the
  wrong type fails, and an unknown key warns with the closest known one (`max_always_token`).
  `apply` still installs such a pack, as before (#135).
