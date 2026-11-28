# Log 149-namespace-core-skills

## engine · intake · done
2026-11-03T13:19:13Z

Campaign gh:113 child 4 of 4, base 148-readme-for-strangers. Size: standard provisional (public contract: skill names users pin; floor standard; may be large after spec). Mode: subagent. Domains: scripting. Targets: offline only. Delivery: normal, oneshot. Ticket names aicfg/config.py: the package is now brainrc/.

## analyst · spec · done
2026-11-03T13:21:05Z

**Did:** spec.md: 9 criteria, 5 open questions with defaults; new area core-skill-names (3 ADDED). Additive design: five `brainrc-` names, old names as deprecated aliases for one minor release, a reserved-name check. Argued size large (~80 files mention the names) with a 3-child Proposed split.
**Open issues:** Q1 collisions unverified (repo has no built-in list): default reserve review, plan, init, help, status, compact and rename all five. Q2 prefix `brainrc-`. Q3 aliases exempt during the window. Q4 removal at the next minor. 

## engine · Spec gate · auto-approved (large → split)
2026-11-03T13:21:05Z

⛔ Spec gate: 149-namespace-core-skills. Size: large (public contract: names users pin; cross-cutting). `--oneshot`: split into 3 local children (specs/tickets/149-1..3), run as `--oneshot`, stacked after child 3 of campaign gh:113: 149.1 → 149.2 → 149.3. Engine wording fix: AC7's parenthetical now reads "a pack's `domains` entry" (no meaning change). living_specs check exit 0.
