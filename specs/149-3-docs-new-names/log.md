# Log 149-3-docs-new-names

## engine · intake · done
2026-11-03T13:46:04Z

Split child 149.3 of gh:149 (campaign member 7), base 149-2-reserved-names. Size: standard (~35 doc files, mechanical). Mode: subagent for the implementer and review. Spec and plan written by the engine from the parent spec (item 3 of its Proposed split, AC7 and AC9); the parent requirement delta is carried here so it applies once.

## engine · Spec gate · auto-approved
2026-11-03T13:46:04Z

## engine · Plan gate · auto-approved
2026-11-03T13:46:04Z

One task; Callouts none.

## implementer · T1 · blocked
2026-11-03T13:55:37Z

**Did:** renamed slash commands and skill uses in shipped docs, rules, agents, skills, sandbox README; Domains links → ../brainrc-aws, ../brainrc-terraform; deprecation note in docs/harness-packages.md; patch fragment.
**Evidence:** validate OK; check_tutorial both modes PASS; README 100 lines; leftover rg hits in scope 9, all legitimate.
**Open issues:** 3 tests outside the fence pin old names: test_planning (Ticket gate `/plan`), test_evals (Domains skills need trigger cases: evals/triggers.toml still expects `aws`/`terraform`), test_plugin_docs (`/brainrc:work`).

## engine · Spec gate · auto-approved (rework 1)
2026-11-03T13:55:37Z

Spec gap: the trigger evals expect `aws`/`terraform` to auto-trigger, but since 149.1 only `brainrc-aws`/`brainrc-terraform` can. Added AC7 (evals and pinned-text tests follow the new names, no assertion dropped) and narrowed the non-goal. living_specs check OK.

## engine · Plan gate · auto-approved (rework 1)
2026-11-03T13:55:37Z

T1 files += evals/triggers.toml, tests/test_planning.py, tests/test_plugin_docs.py. Engine made the edits: 7 trigger cases renamed (expect/forbid), test_planning regex and test_plugin_docs string pin the new names, docs/install.md aligned to `/brainrc:brainrc-work`.

## engine · T1 · done
2026-11-03T13:55:37Z

**Evidence:** tests.test_planning, test_evals, test_plugin_docs OK; full suite 771 OK (1 skipped); validate OK; check_tutorial both modes PASS.
