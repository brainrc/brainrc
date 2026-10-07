## Summary
When a harness is disabled, `apply` now takes ai-config's hooks back out of its settings file. Closes #42.

Before, disabling `claude` and running `apply` removed the links and the hooks directory, but left hook entries in `~/.claude/settings.json` that ran a script that no longer existed.

- **`plan()`:** for each disabled harness with a `settings` path, it adds a merge with no fragments. The existing merge then removes only the groups ai-config owns. Other tools' hooks and other keys stay, and a backup is written first.
- **No settings file, or none of ai-config's hooks in it:** nothing is written.
- **`merge_settings`:** it now drops the `hooks` key when ai-config emptied it, so an uninstall gives back the original file exactly. A user's own empty `"hooks": {}` is kept.
- **`doctor`:** it reports `~/.claude/settings.json has ai-config's hooks but claude is disabled` until `apply` runs.
- **`docs/troubleshooting.md`:** Uninstall loses its manual step.

One behaviour to know about: if a disabled harness's settings file is invalid JSON, `apply` now reports it as a `CONFLICT`, as it already does for enabled harnesses.

## Acceptance criteria
- [x] AC1 only ai-config's groups are removed, others kept, backup written; uninstall restores the original file exactly
- [x] AC2 `status` shows `MERGE` and writes nothing
- [x] AC3 a missing or clean settings file is left alone
- [x] AC4 `doctor` flags leftovers until `apply`
- [x] AC5 doc, VERSION 0.3.9, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK. 5 new tests: 3 failed on assertions first, and 2 are regression guards.
- `python3 scripts/aicfg.py validate` and `validate --pack examples/pack-acme` → OK.
- Real uninstall in a fake home directory: settings back to `{"theme": "dark"}`, 0 links, doctor clean.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
