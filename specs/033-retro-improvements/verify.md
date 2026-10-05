# Verify: Apply the first five retros to spec-agent

Run at 2026-10-05T17:28:27Z on commit `2f2050b`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 59 tests |
| Validate | `python3 scripts/aicfg.py validate` (links, references, CHANGELOG/VERSION) | pass |
| Validate (example) | `python3 scripts/aicfg.py validate --pack examples/pack-acme` | pass (0.3.1 inside >=0.3, <0.4) |
| Context cost | `python3 scripts/aicfg.py tokens` | spec-agent 10449 → 10883 on use; always-loaded unchanged (2664) |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `references/sizing.md` "Changed lines" note (Files column only, ~30 lines, example/doc files half, floors and other columns still apply) | pass |
| AC2 | `references/lifecycle.md` § Gate presentation: `Changes:` diff stat before `Artifacts:` | pass |
| AC3 | `lifecycle.md` intake step 3 (open PRs touching VERSION/CHANGELOG, recommend waiting, one-line skip) and deliver re-check | pass |
| AC4 | `state.md` schema + rule (missing = unknown), `SKILL.md` Run steps 3–4, `templates/retro.md` agent vs wait | pass |
| AC5 | `agents/code-reviewer.md` Check item 2 | pass |
| AC6 | `lifecycle.md` intake step 8 names fallback and `aicfg apply` | pass |
| AC7 | one-to-four-line edits; +434 tokens on use; tests and validate pass; 0.3.1 with CHANGELOG entry | pass |

## Notes
- Docs-only change: verified by reading each section against its criterion plus validate.
