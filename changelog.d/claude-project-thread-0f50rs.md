---
bump: patch
---
- `brainrc new pack <name>` starts a pack that validates on its first run: `pack.toml` pinned to
  this core's minor series, a README, an `AGENTS.md` for whoever edits it (with `CLAUDE.md` and
  `GEMINI.md` pointing at it for those tools), a first rule, a facts skill, a tripwire, pack tests,
  a CI workflow and a pre-commit config pinned to this core's tag, and a `.gitignore`. In a terminal
  it asks for the name, prefix, harnesses and ticket system; a ticket system becomes an
  `[extensions.gatework.ticket]` table. It is written by the same writer as `brainrc import`, and
  the tutorial's first three pack steps are now this one command (#150).
- `brainrc import` and `brainrc new pack` check every naming rule (reserved, vendor and look-alike
  names too) before they write a pack, not only in the `validate` that follows.
- The pack docs are split by what you came for: the tutorial, how-to guides (use, import, validate
  in CI, and start an employer, team, personal or stack pack, or one from a Claude Code plugin),
  the reference in `docs/packs.md`, whose key tables are generated from the JSON Schemas, and an
  explanation of why packs exist and what you trust when you turn one on. Each page states its
  type, and a test keeps the tables, the types and the nav in step (#152).
