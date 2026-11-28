# Retro: 096-keep-mode-follow-symlinks

Ticket: gh:96 · Size: standard · PR: https://github.com/brainrc/brainrc/pull/212

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 5:08 to the stack Deliver gate = 5:06 agent and sibling time + 0:02 waiting at this child's gates; stack gate wait 1 min (shared) |
| Time per stage | spec 2 min, plan 0 min, implement + verify 57 min (agent time, gate waits excluded; verify start not recorded) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 2 (no parallel waves: fallback mode) |
| Review first-pass rate | 3/3 (100%) |
| Retries | 0 |
| Interventions | 0 |
| Review context | shared |
| Criteria passed | 7/7 |

## Reflections
Asked once for campaign gh:92 at delivery; answers recorded here if given.
1. skipped (not answered yet)
2. skipped (not answered yet)
3. skipped (not answered yet)

## Proposed improvements
- Installed `~/.claude/skills/spec-agent` and `~/.claude/agents/*` link to a stale `~/projects/ai-config` copy, which forced fallback mode for the whole campaign. Re-run `python3 scripts/aicfg.py apply` from this checkout.
- architect role: when a plan changes a `settings.fragment.json`, include `tests/test_aicfg.py` (pinned hook commands) and the generated `.claude-plugin/plugin.json` / `.cursor-plugin/hooks.json` (regenerated with `aicfg plugin`) in the task's files. gh:98 T1 hit the fence on this.
- verifier role: for install or upgrade behavior, add one real cross-version install (here, pip venvs on 3.12 then 3.13). It caught a wrong doc claim in gh:99.
- ticket-github connector: `gh pr view --json headRefOid` isn't available in every `gh` version; read the head sha from the pushed branch.
