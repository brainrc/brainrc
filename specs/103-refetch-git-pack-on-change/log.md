# Log: 103-refetch-git-pack-on-change

## engine · intake · done
2026-10-27T02:35:56Z

**Did:** Child 4 of campaign gh:93. Branch 103-refetch-git-pack-on-change from 102-apply-validates-packs. ticket.md from gh:103. Size standard (packs.py, cli.py, doctor.py, tests; choice of where to record the fetch and how to treat old clones), mode fallback, domains: scripting, offline only (tests use local bare repos).

**Evidence:**
- read aicfg/packs.py: `fetch_pack` runs only when the clone dir is missing (`_sync` pending list); `_git` has no timeout

**Changed files:** specs/103-refetch-git-pack-on-change/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-27T02:35:56Z

**Did:** Wrote spec.md: 7 criteria (ref and URL change refetch, status reports, doctor flags, no refetch when unchanged, 60s timeout, old clones). Adds two requirements to aicfg-config.

**Evidence:**
- `living_specs.py check` (below)

**Changed files:** specs/103-refetch-git-pack-on-change/spec.md

**Open issues:** 1 (old clones: fetch once, default)

**Next:** Spec gate
