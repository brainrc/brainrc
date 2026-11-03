# Log 147-ci-matrix

## engine · intake · done
2026-11-03T05:59:09Z

Campaign gh:113 child 2 of 4, base 146-oss-project-files. Size: standard (workflow plus maybe a script; floor: CI pipeline change). Mode: subagent. Domains: ci-pipelines, scripting; infra-reviewer joins review. Targets: offline only (CI cells on macOS/Windows can only run after push). Delivery: normal, oneshot. Baseline: inherited from child 1 (725 OK).

## analyst · spec · done
2026-11-03T06:00:11Z

**Did:** spec.md: 8 criteria, 3 open questions with safe defaults; new living area `ci` (2 ADDED).
**Evidence:** docs/install.md Platforms: macOS and Linux, Windows via WSL (symlinks); docs/tutorial.md is prose.
**Open issues:** Q1 Windows cells non-blocking (continue-on-error) with follow-up; Q2 ruff, pyright, coverage not added (new deps need owner approval), follow-up; Q3 tutorial check covers steps 1, 2, 4, 5.
**Next:** architect.

## engine · Spec gate · auto-approved
2026-11-03T06:00:11Z

⛔ Spec gate: 147-ci-matrix. 9-cell matrix with Windows non-blocking, gitleaks once, stdlib tutorial check read from the doc. Ruff, pyright and coverage deferred (Callout safe default: no new dependency). living_specs check exit 0.

## architect · plan · done
2026-11-03T06:02:17Z

**Did:** plan.md with 2 tasks: T1 scripts/check_tutorial.py + tests (AC5, AC6, AC8); T2 validate.yml matrix + changelog (review: each, after T1). The script runs the tutorial in a copy of the checkout under a temp HOME, since step 5 writes packs.local.toml into the core checkout.
**Evidence:** actionlint, zizmor, shellcheck not installed; PyYAML present locally for an ad hoc parse.
**Open issues:** Callouts none. macOS/Windows cells observable only after push.
**Next:** T1, then T2.

## engine · Plan gate · auto-approved
2026-11-03T06:02:17Z

⛔ Plan gate: 147-ci-matrix. 2 sequential tasks; T2 reviewed on its own (CI config) by code-reviewer and infra-reviewer.
