# Verify: Claude Code plugin and marketplace

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_plugin_manifest_comes_from_the_repo`, `test_marketplace_lists_the_repo_as_the_plugin`, `test_plugin_command_writes_once`; real `aicfg plugin` twice: `WROTE` ×2, then `Plugin manifests up to date.` | pass |
| AC2 | `test_validate_fails_on_missing_or_stale_manifests`; real: bumping `VERSION` to 0.3.14 made `validate` print `ERROR .claude-plugin/marketplace.json: stale …; run python3 scripts/aicfg.py plugin` | pass |
| AC3 | `claude plugin validate .` (CLI 2.1.292): passed; only warning is the root `CLAUDE.md` note | pass |
| AC4 | README `### Claude Code plugin (no clone)` with the coverage table and pick-one note; `docs/packs.md` § Packs and Claude Code plugins; `docs/troubleshooting.md` double-install symptom; AGENTS.md and CONTRIBUTING say to run `aicfg plugin` after a `VERSION` bump | pass |
| AC5 | `SKILL.md` subagent mode: `ai-config:<role>` when `<role>` isn't found | pass |
| AC6 | 4 new tests, red first on a stub (assertion failures); VERSION 0.3.14, CHANGELOG; manifests at 0.3.14 | pass |

## Real install (fresh fake HOME, this session's config untouched)
- `claude plugin marketplace add <repo>` → added; `claude plugin install ai-config@ai-config` →
  installed, enabled, version 0.3.13 (before the bump).
- In the installed copy, `skills/spec-agent/roles -> ../../agents` is preserved and resolves.
- The installed `guard_outward.py` asks on `git push origin main` and allows `git status`. Size 2.2 MB.

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK; `validate --pack examples/pack-acme` → OK
