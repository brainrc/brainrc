## Summary
`aicfg` now installs without a clone (#50; refs #50):

```bash
uv tool install git+https://github.com/bxker/ai-config   # or: pipx install git+https://github.com/bxker/ai-config
aicfg apply
```

- **`pyproject.toml`.** `hatchling` is a **build-time only** dependency; at runtime aicfg stays stdlib-only, Python 3.11+. The wheel bundles core's `skills/`, `agents/`, `rules/`, `overrides/`, `mcp/`, the TOML files, `VERSION` and `CHANGELOG.md` as `aicfg/_core/`. The version comes from `VERSION`, and the console script is `aicfg`.
- **Installed mode** (`aicfg/_core` exists):
  - links point into the installed package, so `uv tool upgrade ai-config` updates every harness;
  - local files live in `~/.config/ai-config/` (`$AICFG_HOME`): `harnesses.local.toml`, `packs.local.toml` and `rules/*.local.md`;
  - a relative pack `path` resolves beside `packs.local.toml`;
  - it never writes inside the package (no in-repo `extensions.md`, no `dist/` cleanup), and `plugin` asks for a checkout;
  - the wheel stores spec-agent's `roles` symlink as copies, so the roles check accepts them and `tokens` counts them once.
- **A checkout works exactly as before.** The fixed-home transcript is identical to the 0.3.19 baseline (600 lines).
- **CI** installs the package and runs `aicfg validate` against its bundled core.
- **Not yet:** packs as packages (a pack is still a local folder), PyPI publishing, and command hints that say `aicfg` instead of `python3 scripts/aicfg.py`.
- `VERSION` 0.3.22.

## Acceptance criteria
- [x] AC1 `pyproject.toml`, bundled `_core`, version, console script
- [x] AC2 bundled core used when installed
- [x] AC3 local files in `$AICFG_HOME`; no writes inside the package
- [x] AC4 real `uv tool install` in a fake home directory
- [x] AC5 tests and a CI install step
- [x] AC6 docs, VERSION, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK (151). The 7 new tests failed first.
- **Real `uv tool install`** from this branch in a fake home directory: `apply`, `doctor` (clean), `validate` and `tokens` all work, and `plugin` exits 1 with a hint. Compared with a checkout run, these are identical:
  - `instructions.md` and `extensions.md`;
  - the OpenCode agent renders;
  - `settings.json`;
  - the link names.
- `tokens` differs only by 43 tokens: the checkout's gitignored in-repo `extensions.md`, which an installed copy correctly never writes. A pack listed in `$AICFG_HOME/packs.local.toml` with a relative path loads.
- **The CI step, simulated:** `pip install .` into a venv, then `aicfg validate` from outside the repo → OK.
- Checkout `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
