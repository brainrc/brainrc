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
