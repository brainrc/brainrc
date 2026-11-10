Quote doctor's rm paths and fix doc drift

Part of epic #94 (E3), 2 of 3, stacked on #263. Retarget to `main` before merging. Closes #105.

## Why
Docs had drifted from the code. The install guide told people to stay on v0.3.29, from before the rename. `overrides/README.md` said only Claude Code was synced. `brainrc doctor` printed `rm` fixes with unquoted paths, so pasting one with a space in the path would fail or remove the wrong thing.

## What changed
- `brainrc doctor` quotes the path in its three `rm` fixes (broken link, unused old home, stray broken link), and in its `validate --pack` and `python3 <hook>` fixes, with a new `shell_path` helper. `~` stays outside the quotes so the shell still expands it, and the helper works from the path's parts, so a sibling of the home directory isn't shortened to a wrong `~` path. Plain paths print exactly as before.
- `docs/install.md` says `git checkout v<X.Y.Z>` with a link to Releases instead of pinning v0.3.29.
- New `tests/test_doc_versions.py`: any release pin in the install docs (`git checkout vX.Y.Z`, `@vX.Y.Z`, `brainrc==X.Y.Z`, `--branch vX.Y.Z`) must match `VERSION`'s major.minor. Historical mentions ("removed in 0.5.0") aren't pins.
- `overrides/README.md` lists what `apply` syncs: Claude Code and Cursor hooks and settings fragments, OpenCode's guard plugin. Codex and Antigravity have none.
- AGENTS.md and the README say to treat the repo as public.

## Acceptance criteria
- [x] AC1: `docs/install.md` pins no release.
- [x] AC2: a test fails on a stale pin in the install docs, naming the line. Verified by `DocVersionTest` (it fails on the old `docs/install.md`).
- [x] AC3: `overrides/README.md` matches `harnesses.toml`.
- [x] AC4: AGENTS.md and the README say to treat the repo as public.
- [x] AC5: doctor's `rm` paths survive a round trip through `sh`, spaces and quotes included. Verified by `ShellPathTest`, `DoctorFixQuotingTest` and `TestHomeFindings.test_unused_old_home_fix_quotes_the_dir`.

## How to verify
```
python3 -m unittest tests.test_doc_versions tests.test_doctor_paths tests.test_doctor_home
python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Campaign, Spec, Deliver. See `specs/105-fix-doc-drift/log.md`.
- The issue says AGENTS.md wrongly calls the repo public. It's still private, but #107 decided it goes public, so the line now says to treat it as public. That holds before and after you flip it.
- "A test checks that docs reference the current major.minor" is read as: release pins in the install docs match it. The docs use a placeholder, so they don't need an edit every release.
- The issue pointed at `doctor.py:118`; that code moved, and all three `rm` fixes are quoted.

## Follow-ups
- The README line here may conflict with the README rewrite in the E6 stack (#259). It's one line.

Spec: `specs/105-fix-doc-drift/spec.md` · Plan: `specs/105-fix-doc-drift/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
