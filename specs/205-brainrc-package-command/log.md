# Log: 205-brainrc-package-command

## engine · intake · done
2026-10-27T18:47:44Z
**Did:** Branch 205-brainrc-package-command from 204-point-urls-brainrc. Size large (public API: distribution, console script and import path change; ~21 Python files plus CI workflows), mode subagent, domains scripting + ci-pipelines, offline only, auto.
**Next:** analyst writes spec.md with a Proposed split; auto stops on size large.

## analyst · spec · done
2026-10-27T18:48:46Z
**Did:** Wrote spec.md (Size: large): 11 criteria, new living area `cli-entry-points`, 6 open questions with defaults, 3-child Proposed split.
**Evidence:** engine ran `living_specs.py check` → exit 0 (would update specs/living/cli-entry-points.md).
**Changed files:** specs/205-brainrc-package-command/spec.md
**Open issues:** spec is over ~60 lines.

## engine · blocked · auto hard stop
2026-10-27T18:48:46Z
Size large: auto mode stops after spec.md and its Proposed split. Spec gate not approved. Nothing pushed.

## engine · resume · owner "resize standard"
2026-10-28T01:39:38Z
Block cleared. Size standard, mode subagent, auto false (resume without --auto: every gate stops). Branch merged 204-point-urls-brainrc (run record) and origin/main (v0.3.50, #229 merged). Proposed split dropped from spec.md.

## engine · Spec gate · presented
2026-10-28T01:39:38Z

## engine · Spec gate · approved
2026-10-28T01:41:32Z
Owner approved; answers: --version "brainrc" (asked about a v prefix; engine recommended none, recorded), shims removed next minor after ship, warning not silenceable.

## architect · plan · done
2026-10-28T01:44:30Z
**Did:** plan.md, 5 tasks (T1-T4 review each, sequential; T5 independent). **Open issues:** Callouts non-empty (public contract); hatchling assumed unavailable — engine found PyPI reachable and edited Test strategy before the gate to build and install the wheel locally at verify.

## engine · Plan gate · presented
2026-10-28T01:44:30Z

## engine · Plan gate · approved
2026-10-28T01:45:06Z
Owner approved, including the public contract change.

## implementer · T1 · done
**Did:** git mv aicfg brainrc; self-refs, usage, --version; scripts/brainrc.py; pyproject; tests import brainrc as aicfg.
**Evidence:** red 5 fail + 1 error (.runs/T1-red.txt); engine re-ran: suite OK, both validates OK, --version → brainrc 0.3.50.
**Changed files:** brainrc/*, scripts/{brainrc,aicfg,evals}.py, pyproject.toml, tests/test_{aicfg,mcp,hooks}.py — within fence.

## code-reviewer · T1 · done
2026-10-28T01:53:09Z
**Findings:** LOW test classes after the __main__ block (fixed by engine); LOW usage lacks --version (fixed by engine); LOW scripts/brainrc.py docstring "no command for usage" is pre-existing (follow-up).
Engine committed 6118369. Follow-up noted: docs/architecture.md and AGENTS.md still describe the aicfg/ package (#209 wording pass).

## test-writer · T2 · done
**Evidence:** 11 tests, 9 fail for the right reason (no deprecated_entry, no aicfg module, no warning); 2 guard existing behavior (.runs/T2-red.txt). **Changed files:** tests/test_cli_entry_points.py.

## code-reviewer (engine inline) · T2 · done
**Findings:** LOW test_ac6_python_m_brainrc accepts exit 0 or 1 (status may report drift on a temp HOME); acceptable. Commit cdefc0f.
