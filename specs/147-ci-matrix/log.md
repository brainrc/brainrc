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

## implementer · T1 · blocked
2026-11-03T06:04:24Z

**Did:** Tests (7) and scripts/check_tutorial.py; red on behavior against a stub.
**Evidence:** real run of steps 1, 2, 4, 5: step 4 fails `domains names unknown skill myteam-protobuf` (step 3 creates that skill); with steps 1-5 all pass.
**Open issues:** spec gap in Q3's default.
**Next:** spec revision.

## analyst · spec revision · done
2026-11-03T06:04:24Z

**Did:** AC5, Q3 and the `ci` ADDED requirement now cover tutorial steps 1-5 (6-7 still excluded).
**Changed files:** specs/147-ci-matrix/spec.md

## engine · Spec gate · auto-approved (rework 1)
2026-11-03T06:04:24Z

⛔ Spec gate: 147-ci-matrix, revision 1: tutorial check covers steps 1-5. living_specs check exit 0.

## engine · Plan gate · auto-approved (rework 1)
2026-11-03T06:04:24Z

Plan step set updated to 1-5 to match the spec (4 lines in plan.md; tasks and files unchanged).

## implementer · T1 · done
2026-11-03T06:06:55Z

**Did:** scripts/check_tutorial.py reads steps 1-5 from docs/tutorial.md and runs them in a temp HOME and a symlink-preserving checkout copy; 7 tests.
**Evidence:** red: 6 assertion failures, 1 error against a stub. tests.test_check_tutorial 7 OK; full suite 732 OK (1 skipped); validate OK; check_tutorial.py PASS steps 1-5 (engine re-ran the module and script: OK, 5 PASS).
**Changed files:** scripts/check_tutorial.py, tests/test_check_tutorial.py
**Next:** T2.

## implementer · T2 · done
2026-11-03T06:12:24Z

**Did:** validate.yml: 9-cell matrix, fail-fast off, job name `validate (<os>, <python>)`, bash default, Windows continue-on-error with comment, gitleaks `if:` ubuntu/3.12, tutorial step; changelog fragment (patch).
**Evidence:** YAML parses (ad hoc PyYAML); validate OK; 732 OK.
**Changed files:** .github/workflows/validate.yml, changelog.d/147-ci-matrix.md

## infra-reviewer · T2 · changes-requested
2026-11-03T06:12:24Z

**Findings:**
- HIGH validate.yml:13: required-check name `validate` disappears → gate job named `validate`. (Branch protection unreadable: API 403 on a private free-plan repo, so none can be set today.)
- MEDIUM validate.yml:17: Windows failure shows green; only logs show it → say so in PR body.
- MEDIUM validate.yml:49: gitleaks `if:` implies success() → `!cancelled() && ...`.
- LOW timeout on Windows; Windows python3 may be missing; no concurrency group; `-latest` labels float.

## code-reviewer · T2+batch · done
2026-11-03T06:12:24Z

**Evidence:** check_tutorial PASS 1-5; 732 OK; validate OK.
**Findings:**
- MEDIUM validate.yml:13: check rename (same as infra HIGH).
- LOW tests/test_check_tutorial.py:87: HOME-empty assertion can't fail → follow-up (T1 file).
- LOW tutorial runs twice per cell → accepted.
- LOW Windows copytree/backslash HOME → non-blocking.

## engine · T2 · retry 1
2026-11-03T06:12:24Z

HIGH from infra-reviewer: T2 back to the implementer with the gate job, gitleaks `!cancelled()`, concurrency group.

## implementer · T2 · done (attempt 2)
2026-11-03T06:15:08Z

**Did:** gate job `validate-gate` (name `validate`, needs the matrix, always(), fails unless result is success via env); gitleaks `!cancelled() && ubuntu && 3.12`; workflow concurrency.
**Evidence:** YAML parses; validate OK; 732 OK.

## infra-reviewer · T2 re-review · done
2026-11-03T06:15:08Z

**Findings:**
- MEDIUM validate.yml:12: one pending run per group on main can drop a middle commit's scan → fixed by engine: group uses `github.sha` for pushes.
- LOW validate.yml:62: `needs.validate.result` with only a continue-on-error Windows failure expected `success` (~75%); verify after push.
Prior HIGH and MEDIUM fixed.

## engine · T2 · done
2026-11-03T06:15:08Z

Engine fix for the MEDIUM (concurrency group per sha on push). YAML parses; validate OK; full suite 732 OK. Committed 29cbb10.

## verifier · verify · done
2026-11-03T06:20:22Z

**Did:** Full suite 732 OK; validate and pack-acme validate OK; check_tutorial PASS 1-5 (also on py3.11 and 3.12); sandbox 2 OK; YAML 3x3 matrix fail-fast off; gitleaks 7 commits no leaks. Wrote verify.md.
**Open issues:** verify after push: 9 cells, macOS tutorial, gate result with a failing Windows cell, pip-install smoke (needs network). AC4/AC7 PR-body parts at document stage.
**Next:** document.
