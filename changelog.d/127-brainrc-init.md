---
bump: patch
---
- New `brainrc init` for the first run: it asks which installed harnesses to manage and writes the answer to `harnesses.local.toml`, keeping the rest of that file as it is. An instructions file you already have (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, ...) would be a `CONFLICT` for `apply`, so `init` copies its text into `rules/adopted-<harness>.local.md`, which every harness loads, and moves the original aside as `<file>.bak-brainrc-<time>`. `--yes` takes the defaults, `--harness` names the harnesses, `--no-adopt` leaves your files alone, and `--dry-run` writes nothing. Without a terminal it needs `--yes` or `--harness`. `init` never runs `apply`.
