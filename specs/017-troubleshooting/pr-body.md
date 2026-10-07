## Summary
Adds `docs/troubleshooting.md`, a how-to organised by symptom. Closes #17.

- **Start:** run `aicfg doctor`.
- **A harness doesn't see something:** run `apply`. Rules are rendered, so every edit to them needs `apply`. After moving the repo, delete the broken links, then `apply`.
- **`CONFLICT`:** move the file into the repo or a pack, or delete it.
- **Pack errors:** a table of the real messages (name collision, prefix, `requires_core`, missing `pack.toml`) and their fixes.
- **Settings backups:** they're named `settings.json.bak-aicfg-<UTC time>`, and the last 5 are kept.
- **Uninstall:** disable every harness and pack, `apply`, then remove ai-config's hooks from `~/.claude/settings.json` by hand (see below).
- **A guard hook blocked something safe or missed something risky:** how to report it, and the two tests a fix needs.

`doctor` now ends with `More help: docs/troubleshooting.md` when it finds a problem. The README links the doc.

**Found while verifying:** disabling the `claude` harness and running `apply` removes the links and the hooks directory, but leaves ai-config's hook entries in `settings.json`, pointing at a missing directory. `doctor` doesn't flag that. The doc gives the manual fix, and a follow-up issue covers fixing it in `apply` and `doctor`.

## Acceptance criteria
- [x] AC1 every symptom from the issue is covered
- [x] AC2 every message reproduced with real packs; uninstall run in a fake home directory
- [x] AC3 README link and doctor pointer (test)
- [x] AC4 VERSION 0.3.8, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` and `validate --pack examples/pack-acme` → OK

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
