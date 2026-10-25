# Plan: Hooks fail open when their file is missing

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** the hook command written into users' settings files changes
  form (still owned via `OWNED_HOOK`, so apply replaces the old one). Pack fragments unchanged.
- **Migrations / data changes:** none; the next `aicfg apply` rewrites the hook groups (AC7).
- **Security triggers touched:** guard hooks now fail open when missing (accepted at Spec gate);
  doctor runs local hook scripts via `subprocess` (argument list, no shell). T1 and T2 get
  `review: each` + security review.
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
**Fail open in the fragments.** Only the JSON fragments change. Claude
(`overrides/claude/settings.fragment.json`), per guard:
`f="{{hooks_dir}}/guard_outward.py"; [ ! -f "$f" ] || python3 "$f"`. Missing file → the test is
true → exit 0, no output. Present → the guard's own exit and output. Cursor
(`overrides/cursor/settings.fragment.json`):
`f="{{hooks_dir}}/guard.py"; if [ -f "$f" ]; then python3 "$f"; else echo '{"permission": "allow"}'; fi`.
POSIX `sh` only. `render_fragment` still substitutes `{{hooks_dir}}` (→ `$HOME/...`), and
`OWNED_HOOK` still matches, so `merge_settings` replaces the old groups (AC7) with no code change.

**Doctor hook check.** New `_hook_findings(merges, skipped)` in `aicfg/doctor.py`, added to
`doctor_findings` after the settings checks. For each enabled merge whose settings file parses,
walk its hook groups. Keep the ones `settings._owned(group, m.markers())` says are ai-config's,
and pull the script path out of each command with `re.search(r'"([^"]+\.py)"', command)`,
expanding `$HOME` with `os.path.expandvars`. Dedupe the paths per harness. Missing →
`FAIL <harness>: hook missing: <path>`, fix `command("apply")`. Present → `subprocess.run(["python3",
path], input="{}", capture_output=True, text=True, timeout=<hook timeout or 5>)`. A non-zero
exit → `FAIL <harness>: hook <path> exits <n>`. A timeout, or `python3` not on PATH → FAIL with
that reason. Running `python3` from PATH matches what the harness runs.

Design choice: guard the fragments rather than rewriting commands in `render_fragment`. The guard
stays visible in the fragment, and pack commands aren't silently rewritten.

## Files
| File | Change |
|---|---|
| `overrides/claude/settings.fragment.json` | fail-open command per guard |
| `overrides/cursor/settings.fragment.json` | fail-open command with allow response |
| `tests/test_hooks.py` | render fragment commands, run them via `sh -c` with hooks present / deleted; old groups replaced |
| `aicfg/doctor.py` | `_hook_findings` |
| `tests/test_aicfg.py` | `DoctorTest`: hook missing, hook broken, clean |
| `docs/troubleshooting.md` | "Every tool call is blocked" / doctor's hook findings |

## Risks
- Doctor running a guard could be slow: the 5s default timeout and dedupe bound it.
- Regex extraction misses pack commands of another shape → no finding (spec non-goal).

## Test strategy
`tests/test_hooks.py`: build commands with `aicfg.render_fragment(FRAGMENT, <tmp hooks dir>)`,
and copy or link the real hooks into the tmp dir. AC2: same decision as `run_hook` for a risky
and a safe Bash call. AC1 and AC3: delete the dir, then exit 0 and the expected output. AC7:
`merge_settings` over a settings file with the old-form groups leaves only the new commands.
`DoctorTest`: delete a hook file through the link target copy (the temp repo), and write a hook that
`sys.exit(3)`s.

## Tasks
- [ ] **T1** [agent: implementer] Fail-open hook commands
  - files: `overrides/claude/settings.fragment.json`, `overrides/cursor/settings.fragment.json`, `tests/test_hooks.py`
  - criteria: AC1, AC2, AC3, AC7
  - review: each
- [ ] **T2** [agent: implementer] Doctor hook check
  - files: `aicfg/doctor.py`, `tests/test_aicfg.py`
  - criteria: AC4, AC5, AC6
  - review: each
  - after: T1
- [ ] **T3** [agent: implementer] Troubleshooting entry for blocked tool calls and hook findings
  - files: `docs/troubleshooting.md`
  - criteria: AC4
  - after: T2
