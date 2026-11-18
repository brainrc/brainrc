# Instructions for AI assistants editing this pack

This repository is mypack, a brainrc pack. Its rules and skills load into other people's agents.

- Every skill, agent, command and MCP server starts with `mypack-`. A skill is
  `skills/mypack-<name>/SKILL.md` with frontmatter `name` (the folder's name) and `description`
  (what it does and when to use it).
- Rules (`rules/NN-topic.md`) load in every session. Keep each short, and write it as a narrower
  case of brainrc's own rules, never against them. Detail belongs in a skill.
- Facts (hosts, repositories, tools, teams) go in the `mypack-facts` skill, not in rules.
- No secrets, tokens, personal emails or home folder paths: write `~` and environment variable names.
- When a fact goes stale, add a tripwire for it in `tripwires.toml`.
- `brainrc new skill|agent|rule|command <name>` adds an item with the prefix and frontmatter filled in.
- After a change, run `brainrc validate --pack .`; it runs `tests/` too.
