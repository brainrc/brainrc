Move the settings home to ~/.config/brainrc and add brainrc migrate

## Why
Local files (git packs, `*.local.toml`, `rules/*.local.md`, rendered instructions and extensions)
lived in `~/.config/ai-config`, named by `AICFG_HOME`, and ignored `XDG_CONFIG_HOME`. With the
tool renamed to `brainrc` (#230), its home moves too, without breaking existing installs.
3 of 6 in epic #199 (rename to brainrc), after #230.

## What changed
- **[pack contract]** The settings home is `BRAINRC_HOME`, else `$XDG_CONFIG_HOME/brainrc`
  (absolute values only), else `~/.config/brainrc`.
- `AICFG_HOME` and an existing `~/.config/ai-config` keep working until 0.5.0, with one stderr
  line per run. The old dir is used whenever no new home exists yet, XDG or not, because old
  installs never read `XDG_CONFIG_HOME`.
- New `brainrc migrate [--dry-run]`: moves the old home to the new one and re-runs `apply`, so no
  link points into the old dir. A symlinked old dir moves as the link. Across filesystems it copies
  beside the target, renames into place, and only then removes the source.
- `migrate` refuses, changing nothing, when: the target isn't empty; `AICFG_HOME` is set without
  `BRAINRC_HOME`; an `apply` holds either lock; the source is `/`, `$HOME` or above it, a file, or
  not a settings home; the target is inside the source; an env value is relative.
- `apply` re-points only the links it made from an old home; any other link into an old dir is
  still a `CONFLICT`.
- `brainrc doctor` warns about a legacy or `AICFG_HOME` home, and about an old dir left beside the
  new one. When the new home is empty it points at `migrate`, not removal.
- spec-agent's `active_run.py` follows the same lookup, silently.
- Docs (install, packs, formats, architecture, harness packages) name the new home.
  `install.md` says how to migrate.

## Acceptance criteria
- [x] AC1: a new install uses `~/.config/brainrc`, verified by `test_ac1_*`
- [x] AC2: `BRAINRC_HOME` wins over `AICFG_HOME`, verified by `test_ac2_*`
- [x] AC3: absolute `XDG_CONFIG_HOME` gives `X/brainrc`; empty or relative falls back; with only the old dir, the old dir is used and warns, verified by `test_ac3_*`
- [x] AC4: a legacy-only install works and warns once on stderr, verified by `test_ac4_*` and the installed end-to-end run
- [x] AC5: `AICFG_HOME` works and warns once, never on stdout or for `--version`, verified by `test_ac5_*`
- [x] AC6: with both dirs, the new one is used and the old one never read, verified by `test_ac6_*`
- [x] AC7-AC13: migrate's move, refusals, dry run, idempotency, `AICFG_HOME` rule, locks, and failing apply, verified by `tests/test_migrate.py` (29) and the end-to-end run
- [x] AC14: doctor's home findings, verified by `tests/test_doctor_home.py`
- [x] AC15: `active_run.py` lookup, verified by `tests/test_active_run.py`
- [x] AC16: all of it on a temp HOME; 525 tests and `validate` pass

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
```
End to end, on a temp HOME with the installed package: create `~/.config/ai-config/` with a
`packs.local.toml` and a `rules/*.local.md`, then run `brainrc apply`, `brainrc doctor`,
`brainrc migrate --dry-run`, and `brainrc migrate`. Check that no link points into the old dir and
the local rule is byte-identical.

## Follow-ups
- The spec's lookup paragraph and AC3 were amended after the Spec gate, with the owner's consent,
  so an XDG user's old install isn't ignored silently.
- `tests/test_aicfg.py` `BrainrcCommandTest` runs with the real HOME, so a developer's legacy dir
  adds stderr noise (pre-existing).
- Windows: moving a dir with an open lock file inside may fail (not supported today).
- Hooks dir names, the MCP ownership file, and backup suffixes move in #207.

Spec: `specs/206-brainrc-settings-home/spec.md` · Plan: `specs/206-brainrc-settings-home/plan.md`
Closes #206
Closes #131
