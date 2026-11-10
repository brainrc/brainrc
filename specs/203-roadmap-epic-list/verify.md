# Verify: Replace docs/roadmap.md with the epic list

Run at 2026-11-10T06:20Z on commit `2727fbc`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 724 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate` | pass: OK (links in `docs/roadmap.md` resolve) |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `gh api` open issues titled "Epic …" plus #63 and #18, diffed against the issue numbers linked in `docs/roadmap.md`: identical, 25 epics | pass |
| AC2 | headings: Wave 0, Owner decisions, Waves 1–4, Added after the waves, Open with every sub-issue closed; each epic's wave checked against its sub-issues' Roadmap IDs | pass |
| AC3 | header line links `[CHANGELOG](../CHANGELOG.md)`; `RoadmapTest.test_points_to_the_changelog_for_shipped_work` | pass |
| AC4 | `RoadmapTest` (fails 2 of 4 on the old page) | pass |

## Notes
- The page is a snapshot of 2026-11-10. It drifts as epics close; the header says closed epics drop off.
- Reviewed inline (one context), so `review_context: shared`.
