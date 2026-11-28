## Summary
Adds `python3 scripts/aicfg.py doctor`, a read-only check of this machine's install. Closes #12.

Each finding is a `FAIL` or `WARN` line followed by its `fix:`. It exits 1 on any FAIL.
- **Renders:** `dist/instructions.md` or `extensions.md` is missing or stale.
- **Links, per installed harness:**
  - missing (more than 3 missing in one harness are grouped into one line);
  - pointing at the wrong item;
  - stale (one `apply` would remove);
  - broken, for example after moving the repo (fix: delete it, then `apply`);
  - a real file or a foreign link where a link belongs.
- **Harness not installed:** a WARN with the `harnesses.local.toml` line that disables it. A WARN doesn't fail the run.
- **Packs:** a missing path or `pack.toml`, an unsatisfied `requires_core`, or a failing `validate --pack`. Packs are checked one at a time, and the other checks still run.
- **Settings:** hooks not merged, or invalid JSON.

Also: on Python older than 3.11, every `aicfg.py` command prints a one-line message instead of a `tomllib` traceback.

Doctor reuses `plan()`, `settings_change()`, the renderers, and `validate`, so it can't disagree with `apply` about what "in sync" means. `plan()` gained an optional `every_src` parameter so a broken pack doesn't make it raise.

## Acceptance criteria
- [x] AC1 read-only (snapshot test)
- [x] AC2 stale or missing renders
- [x] AC3 missing, wrong, stale, broken, and conflicting links
- [x] AC4 a harness that isn't installed is a WARN, and its checks are skipped
- [x] AC5 broken or incompatible packs, with the other checks still running
- [x] AC6 unmerged hooks, invalid settings JSON
- [x] AC7 Python 3.11 import guard
- [x] AC8 output format and exit codes
- [x] AC9 docstring, README, VERSION 0.3.7, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK. 16 new tests, each seen failing on an assertion first.
- `python3 scripts/aicfg.py validate` and `validate --pack examples/pack-acme` → OK.
- A real `doctor` run on a machine where `apply` has never run → 4 problems, 4 warnings, exit 1.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
