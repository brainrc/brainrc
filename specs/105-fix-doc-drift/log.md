# Log: 105-fix-doc-drift

## engine · intake
gh:105 via ticket-github, child 2 of 3 in campaign gh:94 (`campaign-094-neutral-core`), branched from 104-local-tripwires. `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size small (doc lines plus one doctor helper; no new dependency), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/105-fix-doc-drift`.
Ticket drift since it was written: overrides/README and AGENTS.md wording partly moved; `doctor.py:118` is now three `rm` fixes; the repo is still private.

## engine · Spec gate · auto-approved
5 criteria (AC1–AC5). Defaults: "treat as public" wording; pins match major.minor or use a placeholder; all three `rm` fixes. `living_specs.py check`: exit 0 (new area `doctor`). Plan stage skipped (small).
