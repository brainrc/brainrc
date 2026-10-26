# Log: 218-github-releases

## engine · intake · done
2026-10-26T03:18:22Z

**Did:** Branch 218-github-releases from main (55d8a21). ticket.md from gh:218. Size standard (CI/CD workflow with contents: write), mode fallback (installed agents link to stale ~/projects/ai-config), domains: ci-pipelines, scripting, offline only.

**Evidence:**
- `python3 -m unittest discover -s tests` → 367 passed (baseline)

**Changed files:** specs/218-github-releases/ticket.md, state.json

**Open issues:** PR CI red on gitleaks until #217 merges.

**Next:** analyst · spec

## analyst · spec · done
2026-10-26T03:19:28Z

**Did:** Wrote spec.md: 6 criteria (notes extraction, missing version error, release created, idempotent, backfill, docs), new living area release.

**Evidence:**
- `living_specs.py check` → OK

**Changed files:** specs/218-github-releases/spec.md

**Open issues:** 1 open question (notes from CHANGELOG vs --notes-out).

**Next:** Spec gate

## architect · plan · done
2026-10-26T03:21:24Z

**Did:** Wrote plan.md: 2 tasks. `release --notes X.Y.Z` reads the section back from CHANGELOG.md; a release.yml step creates the Release unless `gh release view` finds it (covers fresh, re-run, backfill).

**Evidence:** read-only inspection of aicfg/release.py, cli.py usage and main, release.yml, ReleaseTest.

**Changed files:** specs/218-github-releases/plan.md

**Open issues:** none. Callouts: new CLI form (read-only); CI workflow with contents: write; next merge creates a public Release.

**Next:** Plan gate

## implementer · T1 · done
2026-10-26T03:24:02Z

**Did:** `release_notes(text, version)` and `cmd_release_notes` in release.py; `cli.main` routes `release --notes X.Y.Z`; usage line added.

**Evidence:**
- red: both new tests fail on assertions (usage, exit 2)
- `python3 -m unittest discover -s tests` → 369 passed
- `python3 scripts/aicfg.py release --notes 0.3.39` → prints the 0.3.39 section, exit 0

**Changed files:** aicfg/release.py, aicfg/cli.py, tests/test_aicfg.py

**Open issues:** none

**Next:** T2

## implementer · T2 · done
2026-10-26T03:35:14Z

**Did:** release.yml: "GitHub Release" step after the tag push: skip if `gh release view` finds it, else `release --notes` → `gh release create --verify-tag`. Header comment updated. CONTRIBUTING § Releases describes the Release and the manual backfill.

**Evidence:**
- step body under `bash -e` with a stub `gh`: no release → view, create with `--verify-tag --title v0.3.39 --notes-file`; exists → view only, "already released"; both exit 0
- notes file passed to create == `release --notes 0.3.39` output (diff empty)
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** .github/workflows/release.yml, CONTRIBUTING.md

**Open issues:** none

**Next:** review T2

## infra-reviewer · T2 · done
2026-10-26T03:35:14Z

**Did:** Blast radius and rollout of the release.yml change (ci-pipelines checklist).

**Findings:**
- LOW .github/workflows/release.yml: if `gh release view` fails for a reason other than "not found" (API outage), the step tries `create`, which fails if the release exists → job red but nothing wrong is published; a re-run fixes it. Plan risk, accepted.
- none higher: the step runs after the tag push (so a failed push never releases), `concurrency: release` serializes runs, and the bot's own push doesn't retrigger.

**Open issues:** none

**Next:** commit T2

## security-reviewer · T2 · done
2026-10-26T03:35:14Z

**Did:** security-checklist Pipelines: script injection, token scope, untrusted input.

**Findings:** none. Only `secrets.GITHUB_TOKEN` is used, through `env:`; no event data reaches `run:`; the version comes from the repo's own VERSION; `contents: write` was already granted; the job runs only on push to main and workflow_dispatch, never on pull_request.

**Open issues:** none

**Next:** commit T2
