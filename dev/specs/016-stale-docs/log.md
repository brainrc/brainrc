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

## verifier · verify · done
2026-10-05T13:43:27Z

**Did:** Mapped AC1–AC5 in verify.md. Drafted pr-body.md and ticket-comment.md (small: no separate document stage needed beyond drafts).

**Evidence:**
- tests 47 OK; validate OK; no stale wording

**Changed files:** `specs/016-stale-docs/verify.md`, `specs/016-stale-docs/pr-body.md`, `specs/016-stale-docs/ticket-comment.md`

**Open issues:** none

**Next:** Deliver gate

## engine · release 0.1.2 · done
2026-10-05T13:52:25Z

**Did:** At the user's request: merged main (brings #4), turned Unreleased into 0.1.2 covering #4 and this PR, VERSION 0.1.2, wrote the every-PR-bumps rule in the CHANGELOG intro and AGENTS.md.

**Evidence:**
- tests OK; validate OK; example pack validate OK (0.1.2 inside ">=0.1, <0.2")

**Changed files:** `VERSION`, `CHANGELOG.md`, `AGENTS.md`

**Open issues:** validate check for VERSION/CHANGELOG agreement goes into #9

**Next:** push; CI
