## Summary
Folds the lessons from the last four spec-agent retros into the agents and references. Closes #44.

- **`agents/verifier.md`:** if a change adds or alters something a person runs, the verifier runs it once for real in a scratch copy, with `HOME` pointed at a fresh empty directory, and never deletes through `$HOME`. In #12, #17 and #42, this caught what the tests allowed.
- **`agents/implementer.md`:** when the code already exists, a failing test is shown by switching off only the new change, never by stashing files (#12).
- **`references/lifecycle.md`:** the done checkpoint is pushed only after CI on the delivered commit finishes. Two quick pushes broke the gitleaks step on #40.
- **`references/sizing.md`:** test lines count about half toward a ticket's changed lines (#39).
- `VERSION` 0.3.10.

## Acceptance criteria
- [x] AC1 verifier real run and fresh fake home
- [x] AC2 implementer: switch off only the new change
- [x] AC3 lifecycle: push the done checkpoint after CI
- [x] AC4 sizing: test lines count half
- [x] AC5 VERSION, CHANGELOG, `validate`, tests

## Testing
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` and `validate --pack examples/pack-acme` → OK

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
