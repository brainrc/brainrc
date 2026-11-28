# Plan: packs from a git URL, fetched by aicfg

No new dependency (`git` via `subprocess`, stdlib). Public surface: a new pack key `git`
(+ `ref`) and a new command `aicfg update`.

## Approach
- `sources._pack_root`: `git` → `$AICFG_HOME/packs/<key>`; `path` and `git` together, or
  neither, is a ConfigError. `sources()` skips an enabled git pack whose clone doesn't exist
  yet (cli and doctor report it).
- New module `aicfg/packs.py`: `git_packs()` lists enabled git packs; `fetch_pack()` does
  `git init` + `fetch --depth 1 origin <ref>` + `checkout --detach FETCH_HEAD` in a temp dir and
  renames it into place (a failed fetch leaves nothing). It updates in place for `update`,
  refusing a clone with local changes (`git status --porcelain`). A URL starting with `-` is
  refused. Errors become ConfigError with git's last stderr line.
- `cli.cmd_sync`: before loading sources, fetch missing git packs (`apply`) or only print the
  FETCH line (`status`). `cli.cmd_update`: refetch all, then `cmd_sync(apply=True)`. `main` and
  the usage text gain `update`.
- `doctor._doctor_sources`: an unfetched git pack is a FAIL (fix: apply).

## Tasks
| id | title | agent | files | criteria |
|---|---|---|---|---|
| T1 | tests first, with a local bare repo | implementer | tests/test_aicfg.py | AC1–AC5 |
| T2 | `packs.py`, sources, cli, doctor | implementer | aicfg/{packs,sources,cli,doctor}.py | AC1–AC4 |
| T3 | real run: installed aicfg, example pack from a bare repo | implementer | none | AC5 |
| T4 | docs and release | implementer | docs/packs.md, packs.toml, README.md, docs/harness-packages.md, CHANGELOG.md, VERSION | AC6 |
