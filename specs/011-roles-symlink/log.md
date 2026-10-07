## analyst · spec · done
2026-10-07T04:34:09Z

**Did:** Spec (standard): decision with recommendation (option 1 + guard), 5 criteria.

**Evidence:**
- intake: tree clean; no open PRs; baseline tests OK
- only symlink in the repo: skills/spec-agent/roles -> ../../agents; used by SKILL.md role table and fallback.md

**Changed files:** `specs/011-roles-symlink/spec.md`

**Open issues:** decision at the Spec gate

**Next:** Spec gate

## planner · plan · done
2026-10-07T04:37:57Z

**Did:** 2 tasks; option 1 + guard approved.

**Evidence:**
- spec approved 2026-10-07T04:37:57Z

**Changed files:** `specs/011-roles-symlink/plan.md`

**Open issues:** none

**Next:** Plan gate

## implementer + verifier + doc-writer · T1, T2, verify, document · done
2026-10-07T04:40:04Z

**Did:** Guard in validate and doctor (aae64f0); Platforms docs and 0.3.12 (8a895c0).

**Evidence:**
- red: 3 assertion failures on a stub (validate output lacked the roles line; doctor "No problems found.")
- tests OK; validate OK; real clone without symlinks reports it, and the suggested fix restores it

**Changed files:** `scripts/aicfg.py`, `tests/test_aicfg.py`, `README.md`, `docs/formats.md`, `VERSION`, `CHANGELOG.md`

**Open issues:** none

**Next:** Deliver gate
