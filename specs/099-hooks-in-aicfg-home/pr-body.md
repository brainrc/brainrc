Copy installed guard hooks into AICFG_HOME

4 of 4 in epic #92 (E1: Safe writes and fail-open hooks).

## Why
An installed `aicfg` linked the hooks dir into `.../lib/python3.X/site-packages/_core/...`. When `uv tool upgrade` or `pipx upgrade` moves the tool to a new Python, that path is gone. Since #98 the guards then fail open, so they are silently off until the next `apply`.

## What changed
- When installed, `apply` copies every core `overrides/<harness>/hooks` dir to `$AICFG_HOME/hooks/core/` and links each `hooks_dir` there. It copies all of them because Cursor's guard runs Claude's guards from the sibling dir. The copy is built in a temp dir and swapped in.
- `Link` has a new optional `copy` field. A copy that no longer matches the package shows as `UPDATE` in `status` and `doctor`. An old link into the package is re-pointed as an `UPDATE`.
- Disabling a harness prunes its link into the copy, and the copy itself is removed once no harness with hooks is enabled.
- Checkouts are unchanged: hooks still link into the checkout.
- `docs/install.md` explains where installed hooks live and what to do after an upgrade.

## Acceptance criteria
- [x] AC1: installed hooks are copied to `$AICFG_HOME/hooks/core` and linked from there, verified by `test_installed_hooks_link_into_a_copy_in_aicfg_home` and a real pip install
- [x] AC2: the guards still run after the package is gone, verified by `test_guards_still_run_after_the_package_is_gone` and a real 3.12 → 3.13 upgrade (Claude `ask`, Cursor `deny`, no re-apply)
- [x] AC3: an upgraded package refreshes the copy, verified by `test_an_upgraded_package_refreshes_the_copy`
- [x] AC4: a checkout still links live, verified by `test_checkout_hooks_link_into_the_checkout`
- [x] AC5: an old link into the package is re-pointed, verified by `test_an_old_link_into_the_package_is_repointed`
- [x] AC6: the copy is removed when no harness with hooks is enabled, verified by `test_disabling_every_hooked_harness_removes_the_copy`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- Found by the real upgrade run, and outside this ticket: after a Python change, skill and agent links into the old venv show as `CONFLICT` (140 here), and `apply` doesn't re-link them. `doctor` gives an `rm` for each, and `install.md` now says so. Suggested fix: treat a dangling link into an old `_core` path as `update`.
- LOW: `doctor` describes a stale hooks copy as "points at the wrong item". The fix it gives (`apply`) is right.
- Spec changes after approval: AC1 and AC6 were revised at a second Spec gate (copy every core hooks dir). A non-goal's wording was corrected after the real run.

Spec: `specs/099-hooks-in-aicfg-home/spec.md` · Plan: `specs/099-hooks-in-aicfg-home/plan.md`
Closes #99
