---
bump: patch
---
- `brainrc new skill <name>` writes a skill into the pack you are in (or the one `--pack` names),
  with the prefix and frontmatter filled in, and checks the pack. `--domain GLOB,...` writes a
  domain skill with its four sections and adds a Domains row for those files to `pack.toml`,
  keeping the rest of the file as written. The tutorial's domain skill step now uses it (#159).
