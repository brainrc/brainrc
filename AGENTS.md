# Instructions for AI assistants editing this repo

This repo is **public** and is the source of truth for the owner's AI harness config.
These rules apply to human contributors too. Setup and PR workflow: [CONTRIBUTING.md](CONTRIBUTING.md).

- Never add secrets, tokens, personal emails, internal hostnames, or absolute
  paths like `/Users/<name>`. Use `~` and environment variable *names*.
- Keep it generic: no employer or client names, internal tools, project keys, or account
  details. That content belongs in a pack (`docs/packs.md`); examples here use "acme".
- Skills: `skills/<name>/SKILL.md` with frontmatter `name` (must equal the directory
  name) and `description` (what it does and *when* to use it).
- Agents: `agents/<name>.md` with frontmatter `name` (must equal the file stem),
  `description`, and optional `tools`.
- Commands: `commands/<name>.md` with frontmatter `description`; use `$ARGUMENTS`.
- Rules: `rules/NN-topic.md`, concatenated in filename order. Keep them
  harness-neutral (no tool-specific syntax like `@imports`).
- Domain skills (`skills/<stack>/`) follow: Validate (offline commands) / Conventions /
  Review checklist / Never without approval. Register new ones in the Domains table of
  `skills/spec-agent/SKILL.md`.
- Agents: frontmatter `model` is `haiku|sonnet|opus|inherit`; keep `tools` least-privilege.
- Keep `scripts/aicfg.py` and hooks stdlib-only (Python 3.11+). New guard patterns need tests
  for both the risky command and a safe near-miss in `tests/test_hooks.py`.
- Keep files short: they are loaded into model context. Rules load every session.
- After changes, run `python3 scripts/aicfg.py validate` and `python3 -m unittest discover -s tests`.
- Every PR bumps `VERSION` (semver, policy in `CHANGELOG.md`) and adds its entries under that
  version in `CHANGELOG.md`. No Unreleased section. Then run `python3 scripts/aicfg.py plugin`.
- Don't edit `dist/` or `.claude-plugin/`; they're generated.
