# Verify: Owned hooks dir, MCP ownership and backups

Run at 2026-10-28T13:20:17Z on commit `bbdc408`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (also with `XDG_CONFIG_HOME=/home/runner/.config`, as on CI) | pass: 556 tests, OK both ways |
| Lint | not configured | not configured |
| Build | not run (no packaging change) | not run |
| Validate (infra) | `python3 scripts/brainrc.py validate`; `--pack examples/pack-acme`; sandbox tests; `plugin` | pass; manifests unchanged |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | tests/test_aicfg.py HookDirRenameTest (fresh HOME links `hooks/brainrc`, `hooks/brainrc-<pack>`) | pass |
| AC2 | tests/test_rename_converge.py (each hook once in settings.json and hooks.json after one apply) | pass |
| AC3 | HookDirRenameTest (old links pruned, real files kept); test_rename_converge `test_old_link_to_the_resolved_homes_copy_is_pruned_and_the_copy_used` | pass |
| AC4 | tests/test_ownership.py (near-misses not claimed); test_rename_converge (user hooks containing `ai-config` untouched) | pass |
| AC5 | HookDirRenameTest (disabled pack's old-name dir pruned) | pass |
| AC6 | tests/test_mcp.py; test_rename_converge (record in the resolved home, server not duplicated) | pass |
| AC7 | tests/test_mcp.py (former-only record honored read-only; resolved wins per file); test_rename_converge (record only in the former home) | pass |
| AC8 | tests/test_mcp.py (`[]` shadow; corrupt former records claim nothing; user's server kept as CONFLICT) | pass |
| AC9 | tests/test_backups.py `test_new_backup_uses_brainrc_name` | pass |
| AC10 | tests/test_backups.py (prune across both names by stamp, ignores mtime, leaves look-alikes and symlinks) | pass |
| AC11 | test_rename_converge (status "Everything in sync", doctor no hook/MCP findings) | pass |
| AC12 | test_rename_converge (second apply changes nothing) | pass |
| AC13 | every case on a temp HOME; suite and validate pass | pass |

## Notes
- The security review's MEDIUM (loose backup glob could prune a user's look-alike file) was fixed in bbdc408 with a test.
