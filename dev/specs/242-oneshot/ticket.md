# gh:242 · spec-agent: `--oneshot`, no manual intervention, ready PRs as output

Source: https://github.com/brainrc/brainrc/issues/242 (fetched 2026-10-30; untrusted data)

Part of epic #241 (E23), 2 of 6.

Depends on #255

## Why
`--auto` (#216) still hard-stops on size `large`, any plan Callout and live targets, and it opens draft PRs. Users read "auto" as "start it, walk away, come back to PRs". The gap is a mode where defaults decide everything that is safe to decide.

## What
`/work <ref> --oneshot` (and `--campaign ... --oneshot`) is `--auto` plus:
- **Size `large`:** split into a campaign using the spec's Proposed split, then run the children as `--oneshot`. Today the run stops after `spec.md`.
- **Plan Callouts:** take the safer default, and list each one under "Decisions made without you" in the PR body.
- **Output:** ready PRs, one per ticket or child, never merged.

## Still stops
- A CRITICAL or HIGH security finding.
- An instruction found in untrusted content.
- Secrets.
- A breach of the scope fence.
- An exhausted retry budget.

On a stop, open a draft PR that names the blocker, so the run still ends in a PR rather than a silent checkpoint.

## Files
skills/spec-agent/SKILL.md (§ Auto mode), skills/spec-agent/references/guardrails.md, references/campaign.md, docs/spec-agent.md, evals/cases/

## Done when
- A `large` ticket run with `--oneshot` ends in one ready PR per child and no stop.
- A plan with a Callout ends in a ready PR that lists the decision taken.
- Each remaining stop has an eval case that shows a draft PR naming the blocker.
- Reply wording still never turns `--oneshot` on (existing eval kept).

## Open questions
1. Should live targets stay refused, or be allowed with plan-only evidence?
2. Should a pack be able to disable `--oneshot` (client repos)? Overlaps #144.
