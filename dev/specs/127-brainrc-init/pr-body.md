Add `brainrc init`: pick harnesses and adopt existing instruction files

Part of epic #109 (E4), 3 of 6, stacked on #<PR_126>. Retarget to `main` before merging. Closes #127.

## Why
On a machine that already has `~/.claude/CLAUDE.md` or `~/.codex/AGENTS.md`, the first `apply` reported a `CONFLICT` and linked nothing there. The shared rules never loaded until you moved your file by hand, and then your own text was gone. Choosing harnesses meant editing harnesses.local.toml yourself.

## What changed
- New `brainrc init`. In a terminal it asks, per installed harness, whether to manage it; `--yes` takes every installed one and `--harness claude,codex` names them. The answer goes into harnesses.local.toml as `enabled = false` / `true` lines, and the rest of that file stays as it was.
- An instructions file apply would call a `CONFLICT` (a real file, or a link brainrc didn't make) is copied to `rules/adopted-<harness>.local.md` and moved aside as `<file>.bak-brainrc-<UTC time>`. Local rules already load in every harness, so `init` then `apply` keeps your text with no CONFLICT.
- Nothing is deleted. A link you made is moved as a link and its target is untouched; a link brainrc made is left alone. The same text in two files, or init run again, is adopted once.
- `--dry-run` writes nothing, and `--no-adopt` leaves your files where they are. Without a terminal, init needs `--yes` or `--harness`. It never runs `apply`, and it's refused like `apply` while an old settings home is unmigrated.
- README and docs/install.md add `init` as the first step.

## Acceptance criteria
- [x] AC1: init then apply: no CONFLICT, and your text loads. Verified by `InitTest`.
- [x] AC2: asks in a terminal; needs `--yes` or `--harness` without one. Verified by `InitTest`.
- [x] AC3: `--harness` writes `enabled` and keeps the rest of the file. Verified by `InitTest` and `SetEnabledTest`.
- [x] AC4: text to `rules/adopted-<harness>.local.md`, original moved aside, links handled. Verified by `InitTest`.
- [x] AC5: identical text adopted once; empty files moved without a rule. Verified by `InitTest`.
- [x] AC6: `--dry-run` and `--no-adopt`. Verified by `InitTest`.
- [x] AC7: refused while an old home is unmigrated. Verified by `InitTest`.

## How to verify
```
python3 -m unittest tests.test_init
python3 -m unittest discover -s tests
HOME=$(mktemp -d) sh -c 'mkdir "$HOME/.claude" && echo mine > "$HOME/.claude/CLAUDE.md" && python3 scripts/brainrc.py init --yes --dry-run'
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Spec, Plan, Deliver. See `specs/127-brainrc-init/log.md`.
- Adopted text is a machine-local rule, so it loads in every harness brainrc manages, not only the one it came from. Delete or edit `rules/adopted-*.local.md` to change that.
- Content profiles (syncer only, recommended, everything) are left to #173, which owns profiles. init meets the ticket's done-when without them.
- No managed-block mode that edits your file in place: adoption already clears the CONFLICT.

## Follow-ups
- Offer #173's profiles in `init` once they exist.
- A managed-block mode, if anyone wants their file kept in place.

Spec: `specs/127-brainrc-init/spec.md` · Plan: `specs/127-brainrc-init/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
