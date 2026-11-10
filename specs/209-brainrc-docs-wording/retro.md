# Retro: 209-brainrc-docs-wording

Ticket: gh:209 · Size: standard · PR: https://github.com/brainrc/brainrc/pull/235

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | see state.json `metrics` |
| Time per stage | see `metrics.stage_started_at` |
| Gate rework (spec / plan / deliver) | 1 / 0 / 0 (engine withdrew a Spec approval: living-spec shorthand) |
| Tasks | 10 (T1-T9, F1); parallel waves: 2 (T2+T3, T4+T5) |
| Review first-pass rate | per-task reviews clean; batched review needed F1 (1 HIGH, 2 MEDIUM) |
| Retries | 0 |
| Interventions | 0 (owner asked for no decisions before Deliver) |
| Criteria passed | 8/8 |

## Reflections
1. skipped
2. None before the Deliver gate, by the owner's choice.
3. skipped

## Proposed improvements
- Engine: never auto-approve a Spec gate before `living_specs.py check` exits 0 (this run's first approval script ran the check and approved regardless).
- analyst role: MODIFIED blocks must carry the full requirement text; add that sentence to the role file, since a wording-only delta invites shorthand.
- Allowlist tests: require a file-specific glob for package code; package-wide rows hid a stale docstring.

## After delivery
- Outcome: merged
- Merged at: 2026-10-28T20:16:04Z
- Post-merge verify: pass (see `verify-merged.md`; tutorial ran clean)
- CI failures: 0 own / 0 external
- Review rounds: 0
- Caught by reviewers, missed by the run's own: none
- Follow-up title: Rename the kept on-disk names (Codex MCP markers, ai-config-guard.js, aicfg-fetched.json)
- Follow-up body: Rename with old-name recognition so existing installs converge on the next apply; shrink the test_old_names allowlist.
