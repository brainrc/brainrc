Move core skills to brainrc-* names, keep the old names as aliases

4 of 6 in epic #113, stacked on #<PREV_PR>. Retarget to `main` before merging. Part 1 of 3 of #149.

## Why
`work`, `review`, `plan`, `aws` and `terraform` can shadow a harness built-in or a user's own skill of the same name. Users type and pin these names, so the change must be additive with a deprecation window.

## What changed
- `skills/brainrc-{work,review,plan,aws,terraform}`: the five skills, moved with `git mv`. Only `name:` changed.
- `skills/{work,review,plan,aws,terraform}`: short deprecated aliases that point to the new skill, say they are removed in 0.6.0, set `disable-model-invocation: true`, and keep `argument-hint`, so `/work`, `/review` and `/plan` still work as before.
- `validate` checks each alias: present, model-disabled, description starts with "Deprecated", names its replacement and the removal release, and its target exists.
- `tests/test_skill_aliases.py`: contract tests and near-misses.
- `changelog.d/149-1-namespaced-skills.md` (patch).

## Acceptance criteria
- [x] AC1, AC3, AC5: new dirs, alias content, one auto-triggerable member per pair (`tests.test_skill_aliases`)
- [x] AC2: `apply` under a temp HOME links both `brainrc-<n>` and `<n>` for Claude Code (verify.md)
- [x] AC4: aliases forward `$ARGUMENTS` and keep `argument-hint` (tests; not run interactively)
- [x] AC6, AC9: old-name links and pack `domains` still resolve; validate and the suite pass (766 OK)
- [x] AC7, AC8: plugin manifests point at `./skills/`, so they carry both names unchanged; stale-manifest and broken-alias near-misses fail validate

## How to verify
```
python3 scripts/brainrc.py validate
python3 -m unittest tests.test_skill_aliases
python3 -m unittest discover -s tests
```

## Decisions made without you
- #149 was sized `large` (a public contract change across ~80 files) and split into 3 stacked children: this one, a reserved-name check, and docs moving to the new names.
- Gates auto-approved: Spec and Plan (and the parent's Spec). See `specs/149-1-namespaced-skills/log.md` and `specs/149-namespace-core-skills/log.md`.
- Prefix `brainrc-` (parent Q2). In the plugin this reads `brainrc:brainrc-work`; redundant but harmless.
- Rename all five, though only `review` and `plan` are believed to match Claude Code built-ins. The repo has no list of built-ins to check against (parent Q1).
- Removal release 0.6.0: this ships as a patch in 0.5.x, so the next minor removes the aliases.
- `aws` and `terraform` aliases no longer auto-trigger; their `brainrc-*` names keep the trigger descriptions.
- Ticket comment not posted.

## Follow-ups
- Antigravity may ignore `disable-model-invocation` (docs/harness-packages.md), so aliases could still auto-trigger there. The stub only points onward. Noted for the docs child.
- Remove the aliases and `DEPRECATED_ALIASES` in 0.6.0.

Spec: `specs/149-1-namespaced-skills/spec.md` · Plan: `specs/149-1-namespaced-skills/plan.md` · Parent: `specs/149-namespace-core-skills/spec.md`

Refs #149

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01Hn6pdU7RJ1sLQqc3fDP7Sa
