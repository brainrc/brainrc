## Why

Epic #110 (E5): each harness can be pointed somewhere else by its own variable, but brainrc always wrote to the default paths. Someone with `CLAUDE_CONFIG_DIR`, `CODEX_HOME` or `XDG_CONFIG_HOME` set got links, hooks and MCP servers where their tool never looks, and `doctor` and `uninstall` checked the wrong place.

**Before:** with `CLAUDE_CONFIG_DIR=/opt/claude`, `brainrc apply` linked skills into `~/.claude` and merged MCP servers into `~/.claude.json`. Codex and OpenCode ignored `CODEX_HOME` and `XDG_CONFIG_HOME` the same way, and an `opencode.jsonc` got a second `opencode.json` next to it.

**After:** `status`, `apply`, `doctor` and `uninstall` use `$CLAUDE_CONFIG_DIR` (including its `.claude.json`), `$CODEX_HOME` and `$XDG_CONFIG_HOME/opencode` when the var holds an absolute path, and the old defaults when it is unset, empty or relative. MCP servers go into an existing `opencode.jsonc`, edited in place so its comments stay.

## What changed

- `harnesses.toml` paths take `${VAR:-default}`. `config.load_harnesses()` resolves it once (`env_default`, `env_dir`), so every command, the #126 manifest (format unchanged) and the hook commands see the same concrete path. Only an absolute value counts, as #131 does for the brainrc home; a value under `~` is stored with `~`.
- #132: the `[claude]` paths follow `CLAUDE_CONFIG_DIR`; `.claude.json` moves inside it, where Claude Code keeps it (checked with Claude Code 2.1.322). Doctor reads Claude Code's plugin files from there too. The manifest's trust check also accepts paths inside a dir a harness var names now.
- #133: the `[codex]` paths follow `CODEX_HOME`.
- #134: the `[opencode]` paths follow `XDG_CONFIG_HOME`. New stdlib `brainrc/jsonc.py` reads JSONC and replaces one top-level key in place; the result is re-parsed before it is written.
- Tests: `tests/test_harness_env.py` runs status → apply → status → doctor → uninstall per harness with the var set, unset and empty. Suites that fake HOME (and both tutorial checks) now drop the three vars, so a developer's or CI runner's value can't send test writes into a real config dir.
- Spec-agent campaign record: `specs/campaign-110-harness-paths/` and one `specs/<slug>/` per sub-issue; living spec `aicfg-apply` gains three requirements.

## How to verify

```bash
python3 scripts/brainrc.py validate
python3 -m unittest discover -s tests
d=$(mktemp -d); XDG_CONFIG_HOME=$d/x CLAUDE_CONFIG_DIR=$d/c CODEX_HOME=$d/o python3 -m unittest discover -s tests; find "$d" -mindepth 1   # prints nothing
```

Closes #132
Closes #133
Closes #134

## Checklist

- [x] Added one `changelog.d/<branch>.md` fragment (`bump:` + bullets); did not edit `VERSION` or `CHANGELOG.md`
- [x] `python3 scripts/brainrc.py validate`
- [x] `python3 -m unittest discover -s tests`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
