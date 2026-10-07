## analyst · spec · done
2026-10-07T04:03:01Z

**Did:** Light spec (small): 5 criteria; design reuses merge_settings with an empty fragment.

**Evidence:**
- intake: tree clean; no open PRs; baseline tests OK

**Changed files:** `specs/042-disabled-harness-hooks/spec.md`

**Open issues:** none

**Next:** Spec gate

## implementer + verifier + doc-writer · T1, verify, document · done
2026-10-07T04:10:48Z

**Did:** Empty-fragment merge for disabled harnesses, doctor message, merge drops emptied hooks key, doc, 0.3.9 (dfa0238).

**Evidence:**
- red: MERGE line missing from status; doctor 0 settings FAILs; {'theme': 'dark', 'hooks': {}} != {'theme': 'dark'}
- tests OK; validate OK (core and pack); real uninstall restores the file exactly

**Changed files:** `scripts/aicfg.py`, `tests/test_aicfg.py`, `docs/troubleshooting.md`, `VERSION`, `CHANGELOG.md`

**Open issues:** none

**Next:** Deliver gate
