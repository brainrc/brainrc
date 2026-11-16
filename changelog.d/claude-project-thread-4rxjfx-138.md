---
bump: patch
---
- Packs can ship their own tests: `test = "tests"` in `pack.toml` names a directory or `.py` file of
  unittest tests, and `validate --pack` runs them in a fresh Python, failing when one fails or none
  is found (`doctor` and `apply` never run them). `brainrc.testing` runs a guard hook as Claude Code
  does, with `assert_denies`, `assert_asks`, `assert_allows` and `assert_no_opinion`, so hook tests
  need no scaffolding of their own; core's hook tests use it too. The homelab example's guard tests
  now live in the pack and run this way, and CI validates both example packs (#138).
