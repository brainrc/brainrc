## Summary
Records the decision for #11 and guards against the failure it describes. Closes #11.

**Decision: keep the `skills/spec-agent/roles` symlink, document supported platforms, and fail loudly on a broken checkout.**
- `aicfg` installs everything by symlink, so rendering `roles/` alone wouldn't make Windows without symlinks work.
- Linking straight to `../../agents` would resolve to folders like `~/.codex/agents`, which don't exist for most harnesses.
- Packaging that copies files (#26) can follow the link at build time.

**Changes:**
- **`validate` and `doctor`:** they now report when `roles` isn't a symlink to `../../agents`, for example a plain file from a clone with `core.symlinks=false`. The message gives the fix. Before this, `validate` printed nine "broken link `roles/…`" errors without a cause.
- **README:** a new Platforms section. macOS and Linux are supported. Windows works through WSL, or with Developer Mode and `core.symlinks` set to true before cloning.
- **`docs/formats.md`:** notes that `roles/` must stay a symlink.
- `VERSION` 0.3.12.

## Acceptance criteria
- [x] AC1 README Platforms
- [x] AC2 `validate` names the cause and the fix
- [x] AC3 `doctor` reports it too
- [x] AC4 `docs/formats.md` note
- [x] AC5 tests, VERSION, CHANGELOG

## Testing
- `python3 -m unittest discover -s tests -q` → OK. 4 new tests, each seen failing on an assertion first.
- Real run: `git clone -c core.symlinks=false` produces the plain file and the new error. The fix in the message (`git config core.symlinks true && git checkout -- skills/spec-agent/roles`) restores the link, and `validate` passes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
