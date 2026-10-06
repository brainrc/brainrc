## analyst · spec · done
2026-10-06T03:51:28Z

**Did:** Light spec (small): 6 criteria from #18 findings 1, 3, 4.

**Evidence:**
- intake: tree clean; no open PRs bump VERSION; baseline tests OK, validate OK

**Changed files:** `specs/018-sandbox-e2e-fixes/spec.md`

**Open issues:** none

**Next:** Spec gate

## implementer · T1 · done
2026-10-06T03:53:27Z

**Did:** 6 tests first (all assertion red), then canary check, message fix, sandbox .gitignore and decoy, docs, VERSION.

**Evidence:**
- red: unknown check kind 'canary' (4), 'expected' in PASS line, stale __pycache__ in README setup
- `python3 -m unittest discover -s tests -q` → OK; validate OK (core and pack)
- real #18 run: sandbox-002 11/0 with decoy; simulated leak → FAIL

**Changed files:** `scripts/evals.py`, `tests/test_evals.py`, `examples/sandbox/.gitignore`, `examples/sandbox/README.md`, `evals/cases/sandbox-002.toml`, `docs/evals.md`, `VERSION`, `CHANGELOG.md`

**Open issues:** none

**Next:** Deliver gate
