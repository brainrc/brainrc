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

## implementer · T3 · done
**Evidence:** entry-point tests 11 OK; suite 455 OK; validate OK. **Changed files:** aicfg/__init__.py, aicfg/__main__.py, brainrc/cli.py, scripts/aicfg.py, pyproject.toml — within fence.

## code-reviewer · T3 · done (no CRITICAL/HIGH)
2026-10-28T02:00:08Z
**Findings:** MEDIUM old ai-config and brainrc both own aicfg/ files and bin/aicfg (uninstalling ai-config after installing brainrc deletes the shims) → release note in T5, docs in #209. MEDIUM -m aicfg warned twice under -W default → fixed (engine). MEDIUM warning named "brainrc" for scripts/aicfg.py → warn_deprecated(old, new), fixed (engine). LOW duplicated 0.5.0 → fixed. LOW stacklevel → accepted.
Engine fixes folded into T3 commit c588355 (within T3 fence). F1 (outside T3 fence, so its own task): -W default regression test; mutation check red (2 != 1) against the pre-fix shim, green after. Commit 7ecd043.

## implementer · T4 · done
**Evidence:** check_install.py in a temp venv: 6/6 PASS; refuses against the checkout (exit 2); suite 456 OK; validate OK. **Changed files:** scripts/check_install.py, .github/workflows/{validate,release}.yml — within fence. Reviews (infra + code) running.

## engine · T5 · done
Fragment written inline (bump minor, [pack contract], 0.5.0 removal, uninstall ai-config first). Commit 6f72cf2.

## infra-reviewer · T4 · done
**Findings:** LOW release.yml first real run is post-merge (failures stop before commit/tag); LOW drop the deprecated aicfg step at 0.5.0. No CRITICAL/HIGH.

## code-reviewer · T4 · changes-requested
**Findings:** HIGH AC3 can pass vacuously (two identical failures); HIGH no finally cleanup, unguarded AC7 import / TimeoutExpired → traceback; MEDIUM AC8 never proves bundled _core is used; MEDIUM AC6 runs --version not status and may compare empty stdout; MEDIUM console scripts from PATH may not match sys.executable; LOW AC7 matches any DeprecationWarning. → T4 attempt 2.

## implementer · T4 · done (attempt 2)
**Evidence:** .runs/T4b-*: 6/6 PASS in temp venv, REFUSE exit 2 (not importable / in checkout), FAIL exit 1 with no traceback after deleting the venv shim; suite 456 OK.

## code-reviewer · T4 re-review · done
**Findings:** all prior findings fixed. LOW import order (fixed by engine); LOW --user installs would REFUSE (accepted: CI uses a normal install). Commit 4487d1b.

## engine · batched review · done
T5 fragment and F1 test reviewed inline: no findings. All other tasks were reviewed one at a time.

## verifier (engine) · verify · done
2026-10-28T02:38:17Z
11/11 criteria pass; see verify.md.

## doc-writer · document · done
docs/install.md install section uses brainrc; PR body and ticket comment drafted. Engine changed the pin example (v0.3.29 predates the rename). Living area cli-entry-points applied.

## engine · Deliver gate · presented
2026-10-28T02:40:22Z

## engine · Deliver gate · approved
2026-10-28T02:45:55Z
Owner approved: push, draft PR, comment on #205.
