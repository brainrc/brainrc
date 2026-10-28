# Verify: Docs and wording pass

Run at 2026-10-28T17:53:05Z on commit `c77a2e6`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (also with `XDG_CONFIG_HOME` set as on CI) | pass: 582 tests, OK (1 skipped as root) both ways |
| Lint | not configured | not configured |
| Build | `python3 scripts/brainrc.py plugin` re-run | pass: manifests current |
| Validate (infra) | `python3 scripts/brainrc.py validate`; `--pack examples/pack-acme`; sandbox tests | pass |
| Plan / diff | `specs/013-tutorial/run-tutorial.sh` (fresh clone, temp HOME) | pass: "tutorial ran clean", no deprecation warnings |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | tests/test_old_names.py `test_only_allowlisted_old_names_remain` passes | pass |
| AC2 | the same test fails on any stale ALLOW row (it did while rows were guesses, before T9) | pass |
| AC3 | T7 commit 8ae2f9f; usage/doctor/errors/banners/guard reasons covered by test_old_names (no hit outside the allowlist) | pass |
| AC4 | T2-T5 commits; test_old_names over docs, README, AGENTS.md, CONTRIBUTING.md, skills, examples, config comments | pass |
| AC5 | run-tutorial.sh exit 0 ("tutorial ran clean"), 14 `brainrc` lines, 0 deprecation lines | pass |
| AC6 | changelog.d/209-brainrc-docs-wording.md: [pack contract], window to 0.5.0, what converges, what doctor flags, kept on-disk names | pass |
| AC7 | suite 582 OK, validate OK; T8 review: pure rename, no behavior change | pass |
| AC8 | living_specs.py apply updated cli-entry-points, aicfg-apply, aicfg-config with the full requirement text | pass |
