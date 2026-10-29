Remove the deprecated aicfg names for 0.5.0

## Why
Since 0.4.0 every old name has warned "removed in 0.5.0". If brainrc simply stopped reading the old settings home,
`apply` would run against an empty new home and drop every pack the user had set up, with no error.

## What changed
- Removed:
  - the `aicfg` console script, `scripts/aicfg.py`, `python -m aicfg` and `import aicfg`;
  - the `aicfg_home` alias and `SHIM_REMOVED_IN`;
  - the CI step that ran `scripts/aicfg.py`.
- `AICFG_HOME` and `~/.config/ai-config` are no longer read. While either holds a home that hasn't been migrated:
  - `status`, `apply` and `update` write nothing, exit 1, and name `brainrc migrate`;
  - `doctor` reports a FAIL with that fix;
  - `migrate` still moves the old home.
- `active_run.py` resolves only the brainrc homes.
- The example pack and the docs' `requires_core` examples allow `<0.6`.
- The docs now point upgrades at `brainrc migrate`.
- Kept: all on-disk convergence (old hook dirs, MCP markers, the guard link, the fetch record, backups) and
  doctor's old-plugin warning.
- This branch also carries #236's changes. That check reads `SHIM_REMOVED_IN`, so its test now patches the
  constant in.

## Acceptance criteria
- [x] AC1: only the `brainrc` script and package; `scripts/aicfg.py` and `aicfg/` are gone; CI doesn't call them
- [x] AC2: `aicfg_home`, `SHIM_REMOVED_IN` and the warning helpers are gone; no deprecation lines
- [x] AC3: `AICFG_HOME` refuses with the exact error and writes nothing
- [x] AC4: a legacy-only home refuses; an existing new home ignores it
- [x] AC5: `migrate` then `apply` works; doctor FAILs; other commands are unaffected
- [x] AC6: `active_run.py` reads only the brainrc homes
- [x] AC7: `requires_core` examples allow `<0.6`
- [x] AC8: `minor` fragment with a [pack contract] bullet; validate passes
- [x] AC9: allowlist is narrow; suite passes with and without XDG; check_install has no aicfg checks

## How to verify
```
python3 -m unittest discover -s tests
XDG_CONFIG_HOME=/home/runner/.config python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
python3 scripts/brainrc.py validate --pack examples/pack-acme
```

## Decisions made without you
- An unmigrated old home makes `status`, `apply` and `update` refuse, rather than brainrc starting fresh.
- The 236 removal-release check stays. It is off while `SHIM_REMOVED_IN` is absent, so a future deprecation can
  reuse it.
- An explicit `BRAINRC_HOME` means no old home counts as unmigrated, so `migrate`'s target flow works.
- Merge order: #236, then 237, then this PR. This branch carries both.
- Local ticket `specs/tickets/238-remove-deprecated-names.md` (there is no GitHub issue).

## Follow-ups
- Packs pinned `requires_core <0.5` must widen their pin to `<0.6` before they work with 0.5.0.

Spec: `specs/238-remove-deprecated-names/spec.md`
