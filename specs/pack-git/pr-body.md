## Summary
Packs now install without a clone (#50; refs #50). A pack entry can name a git URL instead of a path:

```toml
[acme]
git = "git@github.com:acme/acme-ai-pack.git"   # private repos use your git credentials
ref = "v1.2.0"                                 # tag, branch, or commit (optional)
```

- **`apply`** fetches a missing git pack once into `$AICFG_HOME/packs/<key>`. The fetch is shallow and detached, and the clone moves into place only when complete, so a failed fetch writes nothing (`ERROR`, exit 1). After that, `apply` works offline.
- **`status`** only prints the `FETCH` it would do, and **`doctor`** reports an unfetched pack.
- **New `aicfg update`** (also `python3 scripts/aicfg.py update`) refetches every git pack at its `ref`, then applies. It leaves a clone with local changes alone, with an error.
- **Guards:** a `git` or `ref` value starting with `-` is refused, and setting both `path` and `git` is an error.
- **Code:** a new `aicfg/packs.py` runs `git` through `subprocess`, so aicfg stays stdlib-only. `path` packs are unchanged.
- **Not in this PR:** Claude plugin `dependencies`, deleting clones of packs removed from config, and warnings about clones that are behind their remote.
- `VERSION` 0.3.23.

## Acceptance criteria
- [x] AC1 `git` + `ref`; one of `path`/`git`; clone under `$AICFG_HOME/packs`
- [x] AC2 `apply` fetches; a failure writes nothing; `status` only reports
- [x] AC3 `aicfg update`; a changed clone is refused
- [x] AC4 `doctor` flags an unfetched pack
- [x] AC5 offline tests and a real run
- [x] AC6 docs, VERSION, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK (159). The 8 new tests use a local bare repo (`file://`, offline).
- **Real run:** `aicfg` installed with `uv tool install` from this branch in a fake home directory, with the example pack served from a bare repo:
  1. `status` prints FETCH and fetches nothing.
  2. `doctor` FAILs with "not fetched yet".
  3. `apply` fetches `v1` and links its skills; `doctor` is then clean.
  4. With `ref = "v2"`, `update` refetches and links the new skill in all five harnesses.
- The checkout transcript matches the 0.3.19 baseline except for the usage text (the new `update` line).
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
