# Log 148-readme-for-strangers

## engine · intake · done
2026-11-03T06:24:22Z

Campaign gh:113 child 3 of 4, base 147-ci-matrix. Size: standard (README rewrite, maybe docs/, real choices on structure and comparison claims). Mode: subagent. Domains: none (docs). Targets: offline only. Delivery: normal, oneshot.

## analyst · spec · done
2026-11-03T06:25:20Z

**Did:** spec.md: 10 criteria, 4 open questions with defaults; new living area project-docs (2 ADDED). Five harnesses confirmed from harnesses.toml (gemini disabled).
**Open issues:** Q1 text transcript, asciinema follow-up; Q2 rulesync only, one-line "also see ruler, dotagents"; Q3 quickstart check as a unit test with shared logic; Q4 compare stable lines only.
**Next:** architect.

## engine · Spec gate · auto-approved
2026-11-03T06:25:20Z

⛔ Spec gate: 148-readme-for-strangers. README leads with one config → five tools, a quickstart executed by a check, a text transcript, a fair "Why not" table, spec-agent second, ≤100 lines. Engine fix: header Size medium → standard (engine-owned field). living_specs check exit 0.

## architect · plan · done
2026-11-03T06:26:38Z

**Did:** plan.md with 3 sequential tasks: T1 `--readme` mode in scripts/check_tutorial.py (shared run(), parse_readme) + CI step; T2 README lead, quickstart, transcript, spec-agent second, fragment; T3 "Why not" table. Stable lines only: `Dry run. Run \`apply\` to write.` and `Everything in sync.`.
**Open issues:** Callouts none. 100-line cap is tight. Comparison cells need a reviewer check.

## engine · Plan gate · auto-approved
2026-11-03T06:26:38Z

⛔ Plan gate: 148-readme-for-strangers. T1 → T2 → T3 sequential (T2/T3 share README.md). Domains add ci-pipelines (T1 touches validate.yml), so infra-reviewer joins the batch review.

## implementer · T1 · done
2026-11-03T06:31:33Z

**Did:** `--readme`, parse_readme (first bash block under `## Quickstart`, git clone lines dropped), shared run(), fixture tests, one CI step.
**Evidence:** red: 8 behavior failures against a stub; full suite 740 OK (1 skipped); validate OK; check_tutorial.py OK. Engine re-ran tests.test_check_tutorial: OK.
**Open issues:** `--readme` fails until T2 adds `## Quickstart` (CI step red mid-branch only). Quickstart runs with cwd = checkout copy at ~/brainrc.
**Next:** T2.

## implementer · T2 · done
2026-11-03T13:03:30Z

**Did:** README lead (five tools, partial support linked), Quickstart run by `--readme`, Install, transcript from a real temp-HOME run, spec-agent below, More absorbs "Try it"; RealReadmeTest + e2e; fragment.
**Evidence:** red: 3 failures, 1 error. Engine re-ran full suite: 746 OK (1 skipped); --readme PASS. Engine fix: the transcript's apply part said "(the same list, now written)", which apply never prints; replaced with real abbreviated apply lines (checked against a temp-HOME run: apply prints the list without the dry-run line).
**Open issues:** README 95 lines; T3 has 5 lines unless More is trimmed.
**Next:** T3.

## implementer · T3 · done
2026-11-03T13:11:18Z

**Did:** `## Why not …` table (chezmoi, GNU Stow, harness plugins, rulesync, brainrc's limits) and an "Also see ruler, dotagents" line; README reflowed to 100 lines, no link dropped.
**Evidence:** 746 OK; validate OK; --readme PASS. Sources: chezmoi and Stow from their GitHub READMEs (homepages 403 via proxy); plugins from code.claude.com/docs/en/plugins; rulesync, ruler, dotagents (getsentry) READMEs.
**Open issues:** dotagents link is getsentry/dotagents (its README: wires skills, MCP, hooks into every agent tool); the research notes cited a different Go package of the same name. Kept getsentry as the closer match; listed in PR decisions.
**Next:** batched review.

## infra-reviewer · batch · done
2026-11-03T13:14:44Z

**Findings:**
- LOW validate.yml:49: a failing README step skips the later sandbox step in that cell (same as the tutorial step) → accepted.
- LOW check_tutorial.py:97: temp HOME isolates HOME-relative writes only; README bash is not sandboxed → follow-up (docstring wording).
No injection finding; runtime far below the timeout.

## code-reviewer · batch · done
2026-11-03T13:14:44Z

**Evidence:** --readme PASS; 746 OK; transcript matches a real temp-HOME run; harness list and anchors match; "Why not" cells match their saved sources.
**Findings:**
- LOW README.md:57: rulesync row could read as "no hooks" → fixed by engine ("ships spec-agent and its guard hooks").
- LOW 100-line cap test trips on any addition → accepted (spec cap).
- LOW quickstart doesn't mention CONFLICT for pre-existing unmanaged files → follow-up (no line budget).
