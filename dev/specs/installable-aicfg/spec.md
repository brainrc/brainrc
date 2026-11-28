# Spec: install aicfg with pipx or uv, no clone

Ticket: gh:50 (refs) · Size: standard (packaging, source location, local files, docs) · Status: approved

## Today
`aicfg` finds core next to its own package (`config.REPO = aicfg/..`) and reads and writes there:
`harnesses.local.toml`, `packs.local.toml`, `rules/*.local.md`, the deprecated in-repo
`extensions.md`, the legacy `dist/` cleanup, and `plugin` writes manifests. An installed package
has none of the content (skills, agents, rules, overrides, TOML files) and lives in a read-only
place.

## Acceptance criteria
- **AC1** `pyproject.toml` (build backend `hatchling`, a build-time dependency only; runtime stays
  stdlib-only, Python 3.11+). The wheel bundles core's content as `aicfg/_core/`: `skills/`,
  `agents/`, `rules/`, `overrides/`, `mcp/`, `harnesses.toml`, `packs.toml`, `VERSION`,
  `CHANGELOG.md`. Version comes from `VERSION`. Console script `aicfg`.
- **AC2** `aicfg` uses `aicfg/_core` when present (installed), else the checkout (unchanged).
- **AC3** Installed mode keeps local files in `$AICFG_HOME` (default `~/.config/ai-config`):
  `harnesses.local.toml`, `packs.local.toml`, and local rules (`rules/*.local.md`). It never
  writes inside the package: no in-repo `extensions.md`, no `dist/` cleanup, and `plugin` says
  to run it from a checkout. Checkout mode is unchanged.
- **AC4** Real install: `uv tool install` from this repo in a fake HOME, then `aicfg apply`,
  `doctor` (clean), `validate`, `tokens`. The links point into the installed `_core`, rendered
  files and settings match a checkout's run, and a pack in `$AICFG_HOME/packs.local.toml` loads.
- **AC5** Tests: source detection, local-file location in both modes, no writes inside the
  package. CI builds the wheel and runs `aicfg validate` from the install.
- **AC6** README install section (`uv tool install git+https://github.com/bxker/ai-config` or
  pipx), `docs/harness-packages.md` order, CHANGELOG, VERSION 0.3.22. Checkout use stays the
  documented default for contributors.

## Not in this step
- Packs as packages: a pack is still a local directory named in `packs.local.toml`.
- Publishing to PyPI: install from the GitHub URL.
- Self-update: users run `uv tool upgrade` or `pipx upgrade`.

## Open choice
**Where core's content comes from when installed:**
- (A, recommended) Bundled in the wheel. No clone, and it works offline after install. Upgrades
  come through the tool's upgrade command.
- (B) The installed `aicfg` clones core to `~/.local/share/ai-config` on first use and updates it
  with `git pull`. That keeps today's `git pull` model, but it is still a clone, which #50 wants
  to avoid.
