## analyst · spec · done
2026-10-05T13:27:19Z

**Did:** Wrote spec.md from gh:16. Roadmap item already done by #5.

**Evidence:**
- grep located the stale lines: docs/spec-agent.md:82, docs/efficiency.md:33, README.md:3-5

**Changed files:** `specs/016-stale-docs/spec.md`

**Open issues:** 5 criteria, 1 open question (resize to small)

**Next:** Spec gate

## implementer · T1 · done
2026-10-05T13:43:27Z

**Did:** Inline (small). spec-agent.md names existing connectors; efficiency.md drops "Already installed here"; README opening states per-harness reach and links the support table; CHANGELOG Unreleased entry.

**Evidence:**
- grep for stale wording → none; tests 47 OK; validate OK

**Changed files:** `docs/spec-agent.md`, `docs/efficiency.md`, `README.md`, `CHANGELOG.md`

**Open issues:** none

**Next:** verify
