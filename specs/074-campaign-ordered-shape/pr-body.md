Add an ordered campaign shape for dependent epic children

## Why
`/work --campaign` only handled near-identical children. An epic of different, dependent children failed the template check, so every child was rejected as a deviant and the user sequenced the runs and PRs by hand.

## What changed
- Campaigns have two shapes. `playbook` is unchanged. `ordered` builds children in dependency order, each with its own Spec and Plan gates, then presents one Deliver gate for the stack. The Campaign gate shows the shape and the order. `--shape playbook|ordered` overrides the detection.
- Dependencies come from a read-only `dependencies` connector op. ticket-local reads `depends_on:` and an epic's `children:`. ticket-github reads the issue dependency API, falls back to `Depends on #N` body lines, and uses sub-issue order. The gate names the source used.
- After approval only the first child's PR opens. Each later PR opens after its predecessor merges: `main` is merged in, tests re-run, and the body reads "N of M, after #X" and links the epic. Merges are detected on resume or when the user says "merged". Nothing polls.
- `campaign.json` gains `shape`, `dependency_source`, and per-member `order`, `depends_on`, and `branch`, plus status `waiting`. The rules live in an `## Ordered shape` section of `campaign.md`, which playbook runs skip.
- The active-run pointer names the child in progress in an ordered campaign.
- New `campaign` eval check kind in `scripts/evals.py`, with unit tests in `tests/test_evals.py`. Sandbox epic `004` and eval case `sandbox-004.toml` exercise it.
- Docs: Campaigns section in `docs/spec-agent.md`, a row in `docs/evals.md`, changelog fragment.

## Acceptance criteria
Most criteria describe engine behavior written in markdown. They were checked by reading the cited text. No ordered campaign has run yet. AC13 and AC18 have executable evidence.

- [x] AC1, AC2, AC17: shape detection, `--shape`, and the gate line (read: `campaign.md`)
- [x] AC3, AC4: topological order, cycle and out-of-epic stop (read, no test)
- [x] AC5, AC16: `dependencies` op for both connectors (read)
- [x] AC6: child branches chain, pointer names the child in progress (read)
- [x] AC7, AC8: one stack Deliver gate, only the first PR (read, fixture state)
- [x] AC9, AC10, AC11: sequential release, upstream propagation, pause on failure (read)
- [x] AC12: `campaign.json` schema and resume (read, fixture matches)
- [x] AC13: sandbox epic order, gates, first-only delivery (fixture `ok` passes `sandbox-004`)
- [x] AC14: `docs/spec-agent.md` describes both shapes (read)
- [x] AC15: pull-only merge check on resume (read, no polling found)
- [x] AC18: `campaign` check, passing case and near-misses (8 unit tests)

## How to verify
```
python3 -m unittest discover -s tests                        # full suite
python3 -m unittest tests.test_evals.CampaignCheckTest -v    # campaign check, 8 tests
python3 scripts/aicfg.py validate
```
Ordered run in `examples/sandbox`: `/work --campaign local:tickets/004-greeting-epic.md`. The order must be 005, 006, 007, and only 005 is delivered (branch recorded, no remote).

## Follow-ups
- No ordered campaign has run yet. The first real runs are the sandbox epic (`sandbox-004`) and then #77 (watch, sub-issues #78-#81), which need depends-on links added.
- Children that differ now select `ordered` automatically (AC1). Confirm at the Deliver gate that this default is intended.
- Commit `1f223b9` is from `024-metrics-rollup`: its retro and done checkpoint, which did not record #82's merge. It touches only `specs/024-metrics-rollup/` and is not part of #74.

Spec: `specs/074-campaign-ordered-shape/spec.md` · Plan: `specs/074-campaign-ordered-shape/plan.md`
Closes #74

🤖 Generated with [Claude Code](https://claude.com/claude-code)
