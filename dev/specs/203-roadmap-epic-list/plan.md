# Plan: Replace docs/roadmap.md with the epic list

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** none (docs), scripting for the test
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Read every open epic and the `Roadmap ID` of its sub-issues through the connector, group by the
lowest wave, and write one line per epic. A unit test checks the line shape offline; the
live comparison with the open epics is verify evidence.

## Files
| File | Change |
|---|---|
| `docs/roadmap.md` | rewrite |
| `tests/test_roadmap.py` | new |
| `changelog.d/203-roadmap-epic-list.md` | new |

## Risks
- The page goes stale as epics close; the header says closed epics drop off, and E3's own child (this one) is the owner of keeping it.

## Test strategy
`tests/test_roadmap.py` for the shape; a `gh api` diff of open epics against the page's links for AC1.

## Tasks
- [ ] **T1** [agent: implementer] Rewrite the roadmap as the epic list, with a shape test
  - files: `docs/roadmap.md`, `tests/test_roadmap.py`, `changelog.d/203-roadmap-epic-list.md`
  - criteria: AC1, AC2, AC3, AC4
