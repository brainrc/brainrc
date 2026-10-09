## Summary
`aicfg` now reports four problems instead of crashing with a traceback. The Rust port's parity runs found them (see `rust/REPORT.md` on the local comparison branch).

| problem | before | now |
|---|---|---|
| dangling `*.md` link inside a skill | `validate`, `tokens` crash | `validate` gives its existing "dangling symlink" error; `tokens` skips it |
| invalid `overrides/<harness>/settings.fragment.json` | `status`, `apply`, `doctor`, `plugin`, `validate` crash | `status`/`apply` print `ERROR …: invalid JSON (…)` and stop with nothing written (as name collisions do); `doctor` lists a FAIL; `plugin` prints `ERROR`; `validate` reports it once |
| unknown `agents_format` | `doctor` crashes | a `doctor` FAIL with the fix |
| new hook events in a fragment | merged in set (hash) order, which changes between runs | existing events first, then new ones in fragment order |

The code is small:
- `plan.invalid_fragments`;
- `FragmentError`, a `ConfigError` raised by `render_fragment`;
- a check of each harness's `agents_format` before `doctor` plans;
- an ordered loop in `merge_settings`;
- `_markdown_under` listing only real files.

`VERSION` 0.3.21.

## Acceptance criteria
- [x] AC1 dangling `*.md` link
- [x] AC2 invalid fragment, in every command
- [x] AC3 unknown `agents_format` in doctor
- [x] AC4 hook event order
- [x] AC5 tests red first; normal output unchanged

## Testing
- `python3 -m unittest discover -s tests -q` → OK (144). All 6 new tests failed first: 5 crashed, 1 showed the wrong order.
- **Normal output unchanged:** the fixed-home transcript (every command, the files written, the rendered files' hashes, `settings.json`) is identical to the 0.3.19 baseline, all 600 lines.
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
