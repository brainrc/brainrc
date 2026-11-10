# Instructions for AI assistants editing this repo

Treat this repo as **public**: it is the source of truth for the owner's AI harness config,
and anything committed here can be read by anyone.
These rules apply to human contributors too. Setup and PR workflow: [CONTRIBUTING.md](CONTRIBUTING.md).

- Never add secrets, tokens, personal emails, internal hostnames, or absolute
  paths like `/Users/<name>`. Use `~` and environment variable *names*.
- Keep it generic: no employer or client names, internal tools, project keys, or account
  details. That content belongs in a pack (`docs/packs.md`); examples here use "acme".
  List your own such terms in `tripwires.local.toml` (`terms = ["..."]`, gitignored):
  `validate` and the pre-commit hook then fail on any tracked file that contains one.
- Skills: `skills/<name>/SKILL.md` with frontmatter `name` (must equal the directory
  name) and `description` (what it does and *when* to use it).
- Agents: `agents/<name>.md` with frontmatter `name` (must equal the file stem),
  `description`, and optional `tools`.
- Commands (packs only): `commands/<name>.md` with frontmatter `description`; use `$ARGUMENTS`.
  Core ships slash commands as skills with `disable-model-invocation: true` and `argument-hint`.
- Rules: `rules/NN-topic.md`, concatenated in filename order, each starting with
  `trigger: always_on` frontmatter (Antigravity needs it; `brainrc` strips it). Keep them
  harness-neutral (no tool-specific syntax like `@imports`).
- Domain skills (`skills/<stack>/`) follow: Validate (offline commands) / Conventions /
  Review checklist / Never without approval. Register new ones in the Domains table of
  `skills/spec-agent/SKILL.md`.
- Agents: frontmatter `model` is `haiku|sonnet|opus|inherit`; keep `tools` least-privilege.
- Keep the `brainrc/` package (run as `scripts/brainrc.py`) and hooks stdlib-only (Python 3.11+);
  `hatchling` in `pyproject.toml` is build-time only. New guard patterns need tests
  for both the risky command and a safe near-miss in `tests/test_hooks.py`.
- Keep files short: they are loaded into model context. Rules load every session.
- After changes, run `python3 scripts/brainrc.py validate` and `python3 -m unittest discover -s tests`.
- Every PR adds one fragment, `changelog.d/<branch>.md` (`bump:` + bullets, see its README).
  Don't edit `VERSION` or `CHANGELOG.md`: the release workflow folds fragments in and tags on merge.
- Don't edit `dist/`, `.claude-plugin/`, `.cursor-plugin/`, or the root `plugin.json`; they're generated.
