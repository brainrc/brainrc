---
bump: patch
---
- `brainrc init`, run from a project folder, finds its CLAUDE.md, AGENTS.md, Cursor rules and Copilot instructions and offers to import them into a pack (`--import` without asking), asks for a starter profile (`--starter minimal|app|infra`: rules only; recommended without Gatework's infrastructure skills; full), and shows the file, hook and token counts before it writes anything (#297).
