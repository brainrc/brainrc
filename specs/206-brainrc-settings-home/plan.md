# Plan: Settings home ~/.config/brainrc and BRAINRC_HOME

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none (stdlib `os`, `shutil`, `pathlib`, `errno`).
- **Public API / contract changes:** new env var `BRAINRC_HOME` and new default home `~/.config/brainrc` (also `$XDG_CONFIG_HOME/brainrc`, closes #131). New command `brainrc migrate [--dry-run]`. `AICFG_HOME` and a legacy `~/.config/ai-config` keep working with one stderr line each, until `SHIM_REMOVED_IN`. This affects users, packs that read `<home>/extensions.md`, and scripts that read `active-run`.
- **Migrations / data changes:** `migrate` moves the user's old home (git packs, `*.local.toml`, `rules/*.local.md`, renders, hooks copy, `active-run`) to the new home. Safety: it refuses while `AICFG_HOME` is set without `BRAINRC_HOME`, refuses a non-empty target, has `--dry-run`, and holds the source's `apply.lock`. It uses one `os.rename` (atomic, byte-for-byte, a symlinked dir moves as the link). On `EXDEV` it runs `copytree(symlinks=True)` into a temp sibling of the target, renames that into place, and only then removes the source. Rollback: `mv ~/.config/brainrc ~/.config/ai-config && brainrc apply` (the legacy fallback picks it up), or set `BRAINRC_HOME` to the old dir.
- **Security triggers touched:** filesystem moves of user data. Only temp HOMEs in tests.
- **Domains:** scripting. Offline only.
- **Environments affected on deploy:** none. Users get it on upgrade; nothing moves until they run `migrate`.
- **Destructive or replacing changes:** `migrate` removes the old dir only after the move or copy succeeds.
- **Changelog bump: `patch`**, with the bullet tagged **[pack contract]**. Packs and spec-agent read `$AICFG_HOME/extensions.md` (docs/packs.md, spec-agent SKILL.md). That path keeps working, because `AICFG_HOME` and the legacy dir are still honoured and the in-repo copy is still written. So the change is additive, not breaking. A `minor` bump would make this 0.5.0, which is `SHIM_REMOVED_IN`: the shims would be due for removal before #207 to #209 land. Owner to confirm.

## Approach
`config.aicfg_home()` keeps its name, so every caller (cli lock, `mcp.owned_file`, `sources` packs, renders, `hooks_copy_root`, `rendered_agents_dir`) follows the new home with no changes. Its body applies the spec order. A new read-only `config.home_origin() -> str` returns `brainrc_env|aicfg_env|xdg|default|legacy`. `config.new_home()` gives the target without `AICFG_HOME` or the legacy dir. `config.former_homes()` lists the old dirs that are not the resolved home.

`cli._dispatch` prints the home warning once, on stderr, for every command except `--version` and `migrate`. It calls `warn_deprecated("AICFG_HOME", "BRAINRC_HOME")` for `aicfg_env`, and prints one line naming the dir and `brainrc migrate` for `legacy`. Doctor adds findings in its existing `(level, what, fix)` format.

There is one real design choice: how apply re-points links into the old dir. `Link.state(roots)` reports a link outside the roots as `conflict`. So `_sync` and `plan()` add `former_homes()` to their roots, and links into the old home become `update`. This also covers re-running `brainrc apply` by hand after AC13. `migrate` lives in a new `brainrc/migrate.py` and reuses `cli._try_lock`. It releases the lock before it calls `cli.cmd_sync(apply=True)`, because apply locks the same file, which has moved into the new home.

`active_run.py` gets its own copy of the order, with no warning.

## Files
| File | Change |
|---|---|
| `brainrc/config.py` | modify: resolution order, `home_origin`, `new_home`, `former_homes` |
| `brainrc/cli.py` | modify: home warning, `migrate` dispatch, former homes in roots, usage text |
| `brainrc/plan.py` | modify: former homes in `plan()` roots |
| `brainrc/migrate.py` | new: `cmd_migrate(dry_run)` |
| `brainrc/doctor.py` | modify: home findings |
| `skills/spec-agent/scripts/active_run.py` | modify: `pointer_file()` order |
| `tests/test_settings_home.py`, `tests/test_doctor_home.py`, `tests/test_migrate.py` | new |
| `tests/test_aicfg.py`, `tests/test_cli_entry_points.py`, `scripts/check_install.py`, `tests/test_active_run.py` | modify: fixtures set `BRAINRC_HOME`, default-home expectations |
| docs, spec-agent SKILL.md/state.md, `changelog.d/206-brainrc-settings-home.md` | home wording only |

## Risks
- Fixtures that set `AICFG_HOME` now get an extra stderr line, so the entry-point test that counts "0.5.0" breaks. Mitigation: switch those fixtures to `BRAINRC_HOME` in T2.
- Something could touch the real HOME. Mitigation: every test sets HOME, unsets the three env vars, and uses a temp dir.
- The empty-target `rmdir` and the rename could race. Mitigation: hold the lock and re-check that the target is empty right before the rename.

## Test strategy
All tests are unit tests with a temp HOME. `test_settings_home.py` covers AC1 to AC6 through `main()` with captured stdout and stderr. `test_doctor_home.py` covers AC14 via `doctor_findings()`. `test_migrate.py` covers AC7 to AC13: byte comparison, a symlink walk under HOME, a lock held from a second fd, and a monkeypatched failing apply. `test_active_run.py` covers AC15. AC16 is the full suite plus `validate`.

## Tasks
- [ ] **T1** [agent: test-writer] Contract tests for home resolution and warnings
  - files: `tests/test_settings_home.py`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6
  - review: each
- [ ] **T2** [agent: implementer] Home lookup, once-per-run warning, fixtures on `BRAINRC_HOME`
  - files: `brainrc/config.py`, `brainrc/cli.py`, `tests/test_aicfg.py`, `tests/test_cli_entry_points.py`, `scripts/check_install.py`
  - criteria: AC1 to AC6, AC16
  - review: each
  - after: T1
- [ ] **T3** [agent: implementer] Doctor home findings (legacy / AICFG_HOME / unused old dir)
  - files: `brainrc/doctor.py`, `tests/test_doctor_home.py`
  - criteria: AC14
  - after: T2
- [ ] **T4** [agent: implementer] `brainrc migrate [--dry-run]`, links re-pointed via former homes, usage text
  - files: `brainrc/migrate.py`, `brainrc/cli.py`, `brainrc/plan.py`, `tests/test_migrate.py`
  - criteria: AC7, AC8, AC9, AC10, AC11, AC12, AC13
  - review: each
  - after: T2
- [ ] **T5** [agent: implementer] active_run.py resolution plus spec-agent home lines
  - files: `skills/spec-agent/scripts/active_run.py`, `tests/test_active_run.py`, `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/state.md`
  - criteria: AC15
- [ ] **T6** [agent: implementer] Docs naming the home, plus changelog fragment (`bump: patch`, [pack contract])
  - files: `docs/install.md`, `docs/packs.md`, `docs/formats.md`, `changelog.d/206-brainrc-settings-home.md`
  - criteria: AC16 (validate passes)
  - after: T3, T4, T5
