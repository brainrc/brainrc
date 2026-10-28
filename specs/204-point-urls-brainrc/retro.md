# Retro: 204-point-urls-brainrc

Ticket: gh:204 · Size: small · PR: https://github.com/brainrc/brainrc/pull/229

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | unknown split: verified at 18:47Z, then waited for the owner's "ship 204"; PR opened 2026-10-28T01:16:33Z |
| Time per stage | intake+spec+implement+verify ~4 min (18:43Z → 18:47Z) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 1 (no parallel waves) |
| Review first-pass rate | 1/1 (100%) |
| Retries | 0 |
| Interventions | 1 (shipped alone while the campaign is blocked) |
| Criteria passed | 3/3 |

## Reflections
1. skipped
2. The owner shipped this child alone because #205 hit the auto hard stop on size large.
3. skipped

## Proposed improvements
- campaign.md: let an auto ordered campaign open the PRs of children before the first blocked
  one, since they don't depend on it. Today one blocked child holds back every verified one.
- Rename epics: a child ticket's "Files" list named files with nothing to change (pyproject URLs,
  manifests). Check a child's file list against the repo when writing the epic.
