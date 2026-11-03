# Log 149-1-namespaced-skills

## engine · intake · done
2026-11-03T13:21:14Z

Split child 149.1 of gh:149 (campaign gh:113 member 5), base 149-namespace-core-skills. Size: standard (public contract, additive). Mode: subagent. Domains: scripting. Offline only. Oneshot.

## analyst · spec · done
2026-11-03T13:22:27Z

**Did:** child spec: 9 ACs (git mv to brainrc-*, alias stubs with disable-model-invocation, /work /review /plan kept, plugin carries both, tests with near-misses). Requirement changes: None (parent delta applied once by 149.3).
**Open issues:** Q1 Domains links hit a stub until 149.3 (default: acceptable). Q2 knowledge-skill stubs point onward (default: enough). Q3 removal release in the text.

## engine · Spec gate · auto-approved
2026-11-03T13:22:27Z

⛔ Spec gate: 149-1-namespaced-skills. Engine edits (no meaning change): `## Requirement changes` reduced to `None.` for the checker (reason kept here: the parent delta is applied once by 149.3). Q3 resolved by default: this change ships as a patch (additive), so 0.5.x carries the aliases and the deprecation text names **0.6.0** as the removal release.

## architect · plan · done
2026-11-03T13:24:15Z

**Did:** plan.md: T1 test-writer contract tests (tests/test_skill_aliases.py), T2 implementer git mv + alias stubs + _check_aliases in validate.py; both review: each. Plugin manifests point at ./skills/, so no regeneration. Alias descriptions ≤ 80 chars (core always-token budget 2656/3000).
**Open issues:** Callout: additive public-contract change; aws/terraform aliases stop auto-triggering (their brainrc-* replacements keep the triggers).

## engine · Plan gate · auto-approved
2026-11-03T13:24:15Z

⛔ Plan gate: 149-1-namespaced-skills. Engine edit before approval: T2 also adds `changelog.d/149-1-namespaced-skills.md` (patch), since AGENTS.md requires a fragment in every PR (the architect had left it to 149.3). Callout handled by the spec's safe default (additive).
