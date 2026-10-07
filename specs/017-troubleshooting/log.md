## analyst · spec · done
2026-10-06T17:02:54Z

**Did:** Light spec (small): 4 criteria; uninstall flow run in a fake HOME first.

**Evidence:**
- intake: tree clean; no open PRs; baseline tests OK
- fake HOME: disabling all harnesses prunes links but leaves ai-config hooks in settings.json

**Changed files:** `specs/017-troubleshooting/spec.md`

**Open issues:** follow-up issue for the leftover hooks (proposed at Deliver)

**Next:** Spec gate

## implementer + verifier + doc-writer · T1, verify, document · done
2026-10-07T03:02:04Z

**Did:** Doctor pointer (test first), troubleshooting doc, README links, 0.3.8 (14e2969); every message and the uninstall flow reproduced in a scratch copy.

**Evidence:**
- red: 'docs/troubleshooting.md' not found in '1 problem(s), 0 warning(s).'
- tests OK; validate OK (core and pack)
- see verify.md for reproductions

**Changed files:** `docs/troubleshooting.md`, `scripts/aicfg.py`, `tests/test_aicfg.py`, `README.md`, `VERSION`, `CHANGELOG.md`

**Open issues:** follow-up issue for leftover hooks (Deliver gate)

**Next:** Deliver gate
