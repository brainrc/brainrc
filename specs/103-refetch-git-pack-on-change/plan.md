# Plan: Refetch a git pack when its ref or URL changes

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none. A new file inside each clone's `.git/`.
- **Migrations / data changes:** clones without a record are fetched once on the next apply (spec Q1).
- **Security triggers touched:** none new. Runs git with config values, as today; the existing
  `-`-prefix refusal stays.
- **Domains:** scripting
- **Environments affected on deploy:** none; users get it on their next `aicfg apply`
- **Destructive or replacing changes:** none (a clone with local changes is still refused)

## Approach
`fetch_pack` (`aicfg/packs.py`) writes `<clone>/.git/aicfg-fetched.json`,
`{"git": <url>, "ref": <ref or "HEAD">}`, after a successful checkout (in the temp clone before
the rename, or in place). Inside `.git/` it is invisible to `git status` and to the pack's
items. New `fetched(root)` reads it (None when missing or unreadable) and
`stale(cfg, root) -> str | None` returns why a clone needs fetching: `not fetched yet`,
`fetched before aicfg recorded it`, `fetched <old ref> from <url>, packs.toml says <new>`, or the
same for the URL; None when it matches. `cli._sync` builds its pending list from `stale(...)`
instead of `not root.exists()`, so `status` prints `FETCH` and `apply` fetches. `doctor`
reports a non-None `stale` for an existing clone as a FAIL with fix `apply`, next to its
"not fetched yet" check.

`_git` passes `timeout=GIT_TIMEOUT` (60) to `subprocess.run` and turns `TimeoutExpired` into
`ConfigError("git <cmd> timed out after 60s")`, which every caller already reports.

Design choice: a JSON file in `.git/` rather than `git config aicfg.*` in the clone: reading it
on every `status` needs no subprocess, and it moves with the clone on the temp-dir rename.

## Files
| File | Change |
|---|---|
| `aicfg/packs.py` | record file, `fetched`, `stale`, `_git` timeout |
| `aicfg/cli.py` | `_sync` pending list uses `stale` |
| `aicfg/doctor.py` | FAIL for a stale existing clone |
| `tests/test_aicfg.py` | `GitPackTest`: ref change, URL change, status, doctor, unchanged, old clone, timeout |

## Risks
- The first apply after upgrading needs the network for each git pack (Q1); offline it fails
  with the git error and writes nothing, as a first fetch does today.
- Ref `HEAD` vs omitted `ref`: both are stored as `HEAD`, so adding `ref = "HEAD"` isn't a change.

## Test strategy
Extend `GitPackTest` (local bare repo with tags v1 and v2). AC5 patches `aicfg.packs.subprocess.run`
to count calls. AC6 patches it to raise `subprocess.TimeoutExpired` and asserts the `timeout=60`
argument on a real call.

## Tasks
- [ ] **T1** [agent: implementer] Record each fetch; refetch, report, and diagnose on a change
  - files: `aicfg/packs.py`, `aicfg/cli.py`, `aicfg/doctor.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC7
- [ ] **T2** [agent: implementer] 60s timeout on git calls
  - files: `aicfg/packs.py`, `tests/test_aicfg.py`
  - criteria: AC6
  - after: T1
