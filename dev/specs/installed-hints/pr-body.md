## Summary
An installed `aicfg` (from `uv tool install` or `pipx`) now names itself in its hints. `doctor`'s fixes and the usage text say `aicfg <command>` instead of `python3 scripts/aicfg.py <command>`. A checkout prints exactly what it did before. This was the follow-up noted on #58.

- A new `config.command(sub)` picks the form, and `doctor` uses it for every hint.
- The usage text swaps `aicfg.py ` for `aicfg ` when installed.
- `plugin`'s hints keep the checkout command, since `plugin` only runs from a checkout.
- `VERSION` 0.3.24.

## Acceptance criteria
- [x] AC1 installed hints and usage say `aicfg`; checkout output unchanged
- [x] AC2 `plugin` hints unchanged
- [x] AC3 test, README, CHANGELOG, VERSION

## Testing
- `python3 -m unittest discover -s tests -q` → OK (160). The new test failed first.
- **Real install:** `uv tool install` from this branch in a fake home directory. `doctor` prints `fix: aicfg apply`, and the usage text starts with `aicfg status`.
- The checkout transcript is identical to 0.3.23's.
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
