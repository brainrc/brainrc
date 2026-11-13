---
bump: patch
---
- Project output is standards-first (#286): every tool gets `.agents/skills/` and the rules block in
  `AGENTS.md`, which Codex, OpenCode, Cursor and Antigravity read. A tool that can't read them names
  its own places in `harnesses.toml` (`project_skills`, `project_instructions`); today that is
  Claude Code, which also gets `.claude/skills/` and a `CLAUDE.md` block importing `AGENTS.md`.
  `harnesses` in `brainrc.toml` picks which tools get their own files. Golden tests pin both trees.
