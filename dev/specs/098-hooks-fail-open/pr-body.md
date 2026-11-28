Let guard hooks fail open and check them in doctor

3 of 4 in epic #92 (E1: Safe writes and fail-open hooks).

## Why
The guard hooks ran as `python3 "<hooks dir>/guard.py"`. When the hooks dir's target went away (checkout moved or deleted, package removed, Python upgraded), `python3` exited 2. Claude Code reads exit 2 as a block, so every tool call was refused until the user edited `settings.json` by hand. `doctor` didn't notice.

## What changed
- The Claude Code hook commands are now `f="<dir>/guard_*.py"; [ ! -f "$f" ] || python3 "$f"`, which skips a missing script and otherwise behaves exactly like the guard. The Cursor commands reply `{"permission": "allow"}` when the guard is missing. The next `apply` replaces the old commands.
- `doctor` reads ai-config's hook commands from each settings file and runs each script once with `{}` on stdin and the hook's timeout. It reports a script that is missing, exits non-zero, times out, or has no `python3` to run it.
- `.claude-plugin/plugin.json` and `.cursor-plugin/hooks.json` were regenerated with `aicfg plugin` (command lines only).
- `docs/troubleshooting.md` has a new section, "Every tool call is blocked, or doctor says hook missing".

**Trade-off:** a missing guard is now off, not blocking. `doctor` is how you find out.

## Acceptance criteria
- [x] AC1: the Claude hook exits 0 with no output when its script is gone, verified by `test_claude_commands_pass_when_the_hooks_are_gone` and a manual run
- [x] AC2: a hook whose script is present behaves like the guard, verified by `test_claude_commands_behave_like_the_guards_when_present` and `test_cursor_commands_behave_like_the_guard_when_present`
- [x] AC3: Cursor replies allow when its guard is gone, verified by `test_cursor_commands_allow_when_the_hooks_are_gone`
- [x] AC4: doctor reports `hook missing`, verified by `DoctorTest.test_missing_hook_script` and a manual run
- [x] AC5: doctor reports a broken hook, verified by `test_broken_hook_script`
- [x] AC6: a healthy install is clean, with each hook run once with `{}`, verified by `test_every_hook_runs_with_an_empty_payload`
- [x] AC7: old-form hook groups are replaced, verified by `test_apply_replaces_old_form_hook_groups`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- MEDIUM (security review): because hooks fail open, an agent can switch the guards off without a lockout. `mv ~/.claude/hooks/ai-config /tmp/x` gets no prompt (`rm -rf` still asks). Suggest having `guard_outward` ask before `mv`, `rm`, or `ln` on the hooks dir and before writes to the harness settings file.
- LOW: `doctor` raises on a hand-edited settings file whose `hooks` isn't an object or whose `timeout` isn't a number. `settings_change` behaves the same today.
- Scope: T1 was widened at a blocked stop, with approval, to update 5 tests that pinned the old command string and to regenerate the plugin manifests.

Spec: `specs/098-hooks-fail-open/spec.md` · Plan: `specs/098-hooks-fail-open/plan.md`
Closes #98
