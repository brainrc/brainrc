# Verify: living-specs

| Criterion | Evidence | Result |
|---|---|---|
| AC1 truth files | `templates/living.md`; `state.md` layout lists `specs/living/<area>.md` and the `living` field; sandbox runs produced `cli.md` and `farewell.md` in that shape. | pass |
| AC2 deltas | `templates/spec.md` has `## Requirement changes` (guidance in a comment the script skips); both sandbox specs use it. | pass |
| AC3 analyst | `agents/analyst.md` reads `specs/living/` (only touched areas) and must state the delta; `lifecycle.md` spec stage says so. Run 2's analyst step listed `cli.md`, read its two requirements, and wrote a MODIFIED against one. | pass |
| AC4 apply step | `lifecycle.md` document stage runs `living_specs.py apply`, records `state.living`, hand-apply fallback in `doc-writer.md`. Script: all-or-nothing, `check` mode, defaults from the run folder. | pass |
| AC5 tests | `tests/test_living_specs.py` 9 tests (add/modify/remove across areas, 10 failure cases each leaving files untouched, same spec twice is an error, `check`, options, template comments). Sandbox, inline, in a scratch copy: 001 then 003 (run 1 merged to main first). Run 2 MODIFIED `Default output` from run 1, ADDED `Version flag`, created `farewell`; re-applying run 1 failed with nothing written. `sandbox-001` eval: 11/11 before the merge, 12/13 after (the only failure is `main_untouched`, from the merge this two-run test needs); the two new checks pass. `sandbox-003`: its `main_untouched` fails for the same reason and its waves check because this run was inline, not subagent. | pass |
| AC6 docs | `docs/spec-agent.md` Living specs section, OpenSpec credit extended, `docs/evals.md`, roadmap, CHANGELOG 0.3.28, VERSION. | pass |

Full suite 209 OK; `validate` core and pack OK. Deviation from the spec: none. Sandbox gates
were approved by the engine itself for the test run; nothing in it was pushed.
