# Plan: Copy hooks into AICFG_HOME

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none. Installed layout gains `$AICFG_HOME/hooks/core/`.
- **Migrations / data changes:** existing installed `hooks_dir` links into the package are
  re-pointed by the next `apply` (AC5); nothing to do by hand.
- **Security triggers touched:** guard availability (where the guards run from); `rmtree` of
  `$AICFG_HOME/hooks/core` only. T1 and T2 get `review: each` + security review.
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** apply replaces and may remove `$AICFG_HOME/hooks/core`,
  which only aicfg writes.

## Approach
`config.hooks_copy_root()` returns `aicfg_home() / "hooks" / "core"`. In `plan.plan()`, when
`config.installed()` and the source is core, the hooks `Link`'s source becomes
`hooks_copy_root() / name / "hooks"`, and the link gets a new optional field
`copy: tuple[Path, Path] | None = (config.REPO / "overrides", hooks_copy_root())`. A checkout
keeps `copy=None` and today's source (AC4).

`Link.state()`: if `copy` is set and `hooks_copy_current(*copy)` is false, the state is `update`
even when the link is right (AC3). Otherwise the state is as today. An old link into the
package is `update` already, because `_core` is a root (AC5). `hooks_copy_current(src, dest)`
(in `plan.py`) compares the relative file set and bytes of every `src/*/hooks/**` against `dest`,
skipping `__pycache__`.

`cli._sync` apply loop: before re-linking a link with `copy`, it calls `_copy_hooks(src, dest)`.
That copies every `src/*/hooks` into a sibling temp dir `.core.aicfg-tmp-<pid>` (ignoring
`__pycache__`), moves the old `dest` aside, renames the temp into place, and removes the old one.
The copy is all of core's hook dirs, because Cursor's guard needs Claude's (spec revision 1).

Removal (AC6): `plan.stale_hooks_copy(links) -> Path | None` returns `hooks_copy_root()` when
it exists and no planned link has `copy`. `cli` prints `PRUNE` and, on apply, `rmtree`s it.
`_managed_target` also accepts `hooks_copy_root() / <h> / "hooks"`, so a disabled harness's
hooks link into the copy is pruned like today's links into the repo.

Design choice: a `copy` field on `Link` instead of a new plan output, so `plan()` keeps its
3-tuple shape (cli, doctor, tests) and doctor's link checks report a stale copy for free.

## Files
| File | Change |
|---|---|
| `aicfg/config.py` | `hooks_copy_root()` |
| `aicfg/plan.py` | `Link.copy`, `hooks_copy_current`, `stale_hooks_copy`, core hooks link to the copy when installed, `_managed_target` |
| `aicfg/cli.py` | `_copy_hooks`; copy before linking; prune the copy |
| `tests/test_aicfg.py` | `InstalledModeTest`: copy + link, package gone → guards still run, refresh, migration, disabled cleanup; checkout test for AC4 |
| `docs/install.md` | installed hooks live in `$AICFG_HOME/hooks/core` and survive upgrades |

## Risks
- `test_apply_never_writes_inside_the_package` must keep passing: the copy is written only
  under `$AICFG_HOME`.
- Between the two renames the dir is briefly missing: guards fail open for that instant (gh:98).

## Test strategy
`InstalledModeTest` (core under a temp `_core`). AC2: apply, then `rmtree` the package, then run
the installed Claude and Cursor commands from the settings files via `sh -c` with a risky payload,
expecting `ask` / `deny`. AC3: edit a hook in `_core`, then status says `UPDATE`, apply makes the
copy equal, and a stale file planted in the copy is gone. AC5: pre-create the old link into
`_core`, then apply reports `UPDATE` and doctor is clean. AC6: disable claude and cursor, then
apply and check the copy is gone. AC4: checkout `SyncFakeHomeTest`, link target is the repo and
there's no `hooks/` in `$AICFG_HOME`.

## Tasks
- [ ] **T1** [agent: implementer] Installed hooks copied to AICFG_HOME and kept current
  - files: `aicfg/config.py`, `aicfg/plan.py`, `aicfg/cli.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC4, AC5
  - review: each
- [ ] **T2** [agent: implementer] Remove the copy when no harness with hooks is enabled
  - files: `aicfg/plan.py`, `aicfg/cli.py`, `tests/test_aicfg.py`
  - criteria: AC6
  - review: each
  - after: T1
- [ ] **T3** [agent: implementer] Install docs: where installed hooks live
  - files: `docs/install.md`
  - criteria: AC1
  - after: T2
- [ ] **F1** [agent: implementer] Correct install.md: dangling non-hook links after a Python upgrade are CONFLICTs, not re-linked by apply
  - files: `docs/install.md`
  - criteria: AC1
  - after: T3
