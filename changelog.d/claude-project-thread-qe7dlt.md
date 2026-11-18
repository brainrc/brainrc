---
bump: patch
---
- `brainrc new skill <name>` writes a skill into the pack you are in (or the one `--pack` names),
  with the prefix and frontmatter filled in, and checks the pack. `--domain GLOB,...` writes a
  domain skill with its four sections and adds a Domains row for those files to `pack.toml`,
  keeping the rest of the file as written. The tutorial's domain skill step now uses it (#159).
- `brainrc new agent <name>` writes an agent with read-only tools (`Read, Grep, Glob`),
  `model: inherit` and a Handoff section in Gatework's handoff format. `--tools` and `--model` are
  checked before anything is written (#160).
- `brainrc new rule <name>` writes `rules/NN-<name>.md` after the pack's last rule, with core's
  rule frontmatter, and prints what it adds to every session against the pack's
  `max_always_tokens` budget (#161).
- `brainrc new command <name>` writes a command with `$ARGUMENTS`. When this machine manages
  Codex, which skips such commands, it says so, and `--as-skill` (offered in a terminal) writes the
  user-invoked skill form instead (#162).
- `brainrc import` reads Windsurf rules: `.windsurfrules`, `global_rules.md` and
  `.windsurf/rules/`. `always_on` rules become rules; `glob`, `model_decision` and `manual` rules
  become skills, a glob rule with a Domains row (#166).
