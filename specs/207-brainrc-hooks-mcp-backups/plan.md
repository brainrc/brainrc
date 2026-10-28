# Plan: Owned hooks dirs, MCP ownership and backups follow the brainrc name

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** user-visible names change. Default `hooks_dir` in `harnesses.toml` becomes `~/.claude/hooks/brainrc` and `~/.cursor/hooks/brainrc`, so pack hook dirs become `hooks/brainrc-<pack>`. Backups become `.bak-brainrc-*`, which `docs/troubleshooting.md` tells users to look for. Packs that use `{{hooks_dir}}` (the documented way) need no change. A pack or user script that hard-codes `~/.claude/hooks/ai-config(-<pack>)` breaks once apply removes the old link. Plugin manifests are unaffected: they use `${CLAUDE_PLUGIN_ROOT}/overrides/...`, not the hooks dir. `config.OWNED_HOOK_MARKER` (internal, no callers in the repo) changes to `/hooks/brainrc/`. Changelog entry is tagged **[pack contract]** with `bump: patch`, following the 0.4.2 home rename.
- **Migrations / data changes:** the first `apply` on an old-name install rewrites settings, `hooks.json` and the MCP ownership record, and removes the old hook links. Rollback: the `.bak-brainrc-*` backups, plus restoring the old `hooks_dir` in `harnesses.local.toml` (owned entries under either name are still recognized).
- **Security triggers touched:** ownership matching decides which hook entries and MCP servers apply replaces or deletes (a wrong match deletes a user's hook or server).
- **Domains:** scripting
- **Environments affected on deploy:** none (each user's machine converges on their next `apply`)
- **Destructive or replacing changes:** old symlinks `hooks/ai-config*` are deleted (symlinks only, and only when they point at a target apply manages). `.bak-aicfg-*` backups beyond the newest 5 are pruned, as `.bak-aicfg-*` backups are today.

## Approach
**Ownership.** Widen `config.OWNED_HOOK` to `/hooks/(?:ai-config|brainrc)(?:-[a-z0-9-]+)?/`. It still matches whole path components, so `/hooks/ai-configs/` and `/hooks/my-ai-config/` stay unowned. `settings._owned`/`merge_settings`, doctor's `_hook_findings` and the disabled-harness merges in `plan.plan` keep using the regex plus `SettingsMerge.markers()`. Old-name and new-name groups are therefore replaced together by the fragment, with no duplicates (AC2, AC4, AC5).

**Rename.** Change both `hooks_dir` entries in `harnesses.toml`. Add `config.former_hooks_dirs(hooks_dir)`, which returns the sibling `ai-config` dir only when the dir is named `brainrc`, so a dir the user set in `harnesses.local.toml` is used as given (Q1). `plan.plan` adds that dir and its `pack_hooks_dir` siblings to the stale candidates. `_managed_target` also accepts a hooks copy under each `config.former_homes()` dir. The existing stale-unlink path in `cli` then removes the old links; real files or dirs are never candidates because only symlinks are removed (AC1, AC3). The hooks copy under the resolved home stays in use by the new link, and `stale_hooks_copy` still removes it once unused. Former-home copies are left for `migrate`.

**MCP.** `mcp._owned()` merges records per file. It reads `mcp-owned.json` from each `former_homes()` dir, read-only, then from the resolved home, and a key in the resolved home wins (AC6, AC7). `record_owned` writes only to the resolved home. It writes `[]` rather than dropping a key while a former home still holds one, so a stale former record can never claim a server the user later adds (AC8). **Backups.** `settings.replace_file` writes `.bak-brainrc-<stamp>`. Pruning matches only `^<name>\.bak-(aicfg|brainrc)-\d{8}T\d{6}Z$` and sorts by (stamp, old name first) (AC9, AC10).

## Files
| File | Change |
|---|---|
| `brainrc/config.py` | modify: `OWNED_HOOK`, `OWNED_HOOK_MARKER`, new `former_hooks_dirs` |
| `brainrc/plan.py` | modify: stale candidates, `_managed_target` |
| `brainrc/settings.py` | modify: backup name and prune |
| `brainrc/mcp.py` | modify: `_owned`, `record_owned` |
| `harnesses.toml` | modify: claude and cursor `hooks_dir` |
| `docs/troubleshooting.md`, `docs/packs.md` | modify: backup name, example dir |
| `tests/test_backups.py`, `tests/test_ownership.py`, `tests/test_rename_converge.py` | new |
| `tests/test_aicfg.py`, `tests/test_mcp.py` | modify: pinned names, new cases |
| `changelog.d/207-brainrc-hooks-mcp-backups.md` | new |

## Risks
- AC3 reading: "copy they led to" is taken as the hooks copy under the resolved home. It is reused, not deleted. The reviewer should confirm this.
- Over-claiming hooks: `/hooks/brainrc-*` is newly owned. Near-miss tests for each AC4 example mitigate this.
- Pinned test names in `test_aicfg.py` are updated, never weakened. Old-name cases stay as legacy coverage.

## Test strategy
Unit tests use a temp HOME for every case (AC13), as `TempRepoCase` does. Ownership regex plus merge: `test_ownership.py`. Backups: `test_backups.py`. MCP records: `test_mcp.py`. End-to-end old-name install, then apply, status, doctor and a second apply with no change: `test_rename_converge.py`. Every task runs the full suite and `validate`.

## Tasks
- [ ] **T1** [agent: implementer] Backups use the brainrc name, prune across both names
  - files: `brainrc/settings.py`, `tests/test_backups.py`, `tests/test_aicfg.py`, `docs/troubleshooting.md`
  - criteria: AC9, AC10
- [ ] **T2** [agent: implementer] Hook ownership covers both dir names, by path component
  - files: `brainrc/config.py`, `tests/test_ownership.py`
  - criteria: AC4, AC5
  - review: each
- [ ] **T3** [agent: implementer] MCP ownership records honored from former homes, read-only
  - files: `brainrc/mcp.py`, `tests/test_mcp.py`
  - criteria: AC6, AC7, AC8
  - review: each
- [ ] **T4** [agent: implementer] Rename hook dirs, prune old links
  - files: `harnesses.toml`, `brainrc/config.py`, `brainrc/plan.py`, `tests/test_aicfg.py`, `docs/packs.md`
  - criteria: AC1, AC3
  - review: each
  - after: T1, T2
- [ ] **T5** [agent: implementer] Convergence tests for an old-name install, plus changelog fragment
  - files: `tests/test_rename_converge.py`, `changelog.d/207-brainrc-hooks-mcp-backups.md`
  - criteria: AC2, AC11, AC12, AC13
  - after: T3, T4
