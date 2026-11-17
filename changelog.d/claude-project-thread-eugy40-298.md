---
bump: patch
---
- New `docs/capabilities.md`: one row per tool with where its skills, rules, agents, commands,
  guard hooks and MCP servers land, and what a repo gets. The table is generated from
  `harnesses.toml` (`brainrc capabilities --write`), and `tests/test_capabilities.py` fails when
  the two disagree (#298).
