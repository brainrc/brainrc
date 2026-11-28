Refetch a git pack when its ref or URL changes

4 of 5 in epic #93 (E2: Config and pack loading).

## Why
A pack named by `git` URL was fetched into `$AICFG_HOME/packs/<key>` only when that directory was missing. Bumping `ref = "v1"` to `"v2"`, or moving the URL, and running `apply` kept the old checkout without a word, and `doctor` said nothing. Only `aicfg update` moved it. A git call against an unreachable host, or one waiting on a credential prompt, hung `apply`.

## What changed
- After each successful checkout, `fetch_pack` writes `{"git", "ref"}` to the clone's `.git/aicfg-fetched.json`, in the temp clone before the rename or in place. Inside `.git/`, `git status` and the pack's items never see it.
- New `packs.needs_fetch(cfg, root)` says why a clone needs fetching: missing, no record, or a different `git` or `ref`. `cli._sync` builds its `FETCH` list from it, so `status` reports the fetch and `apply` runs it. `doctor` reports it as a FAIL (``pack acme: fetched ref `v1`, packs.toml says `v2` ``).
- `_git` passes `timeout=60` and reports `git <cmd> timed out after 60s` as an error.
- `docs/packs.md` describes the new behavior. The `aicfg-config` living spec gets "Git packs follow their config" and "Git calls time out".

## Acceptance criteria
- [x] AC1: a ref change is fetched and linked by apply, verified by `GitPackTest.test_apply_follows_a_ref_change`
- [x] AC2: status shows the FETCH line without fetching, verified by the same test
- [x] AC3: a URL change is fetched from the new URL, verified by `test_apply_follows_a_url_change`
- [x] AC4: doctor flags a mismatched clone, verified by `test_doctor_flags_a_clone_that_doesnt_match`
- [x] AC5: unchanged config makes no git call, verified by `test_unchanged_config_does_not_fetch`
- [x] AC6: git calls time out after 60s, verified by `test_a_hung_git_call_times_out` and `test_git_calls_have_a_timeout`
- [x] AC7: a clone without a record is fetched once, verified by `test_a_clone_without_a_record_is_fetched_once`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- The first `apply` after upgrading fetches every existing git pack once and needs the network. This was chosen at the Spec gate.
- A refetch runs before the later pack checks, so an `apply` that then fails has already moved the clone. First fetches have always worked this way.
- 60s could cut off a very slow first clone (fetches are shallow). `GIT_TERMINAL_PROMPT=0` would fail a credential prompt at once instead of waiting.

Spec: `specs/103-refetch-git-pack-on-change/spec.md` · Plan: `specs/103-refetch-git-pack-on-change/plan.md`
Closes #103
