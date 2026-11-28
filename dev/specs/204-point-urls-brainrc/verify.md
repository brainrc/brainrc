# Verify: Point URLs and manifests at brainrc/brainrc

Run at 2026-10-27T18:47:04Z on commit `9af5a4c`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 438 tests, OK |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: OK, 26 skills, 9 agents |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `grep -rn "bxker/ai-config" --exclude-dir=specs --exclude-dir=.git --exclude=CHANGELOG.md .` → no output, exit 1 | pass |
| AC2 | `tomllib` read of `[project.urls]` → Repository `https://github.com/brainrc/brainrc`, Issues `https://github.com/brainrc/brainrc/issues` | pass |
| AC3 | `python3 scripts/aicfg.py plugin` exit 0, then `git status` shows no change under `.claude-plugin/`, `.cursor-plugin/`, `plugin.json`; validate and tests pass (above) | pass |

## Notes
Docs and metadata only. The plugin manifests carry no repo URL, so regenerating them changes nothing.
