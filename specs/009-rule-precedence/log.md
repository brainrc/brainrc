## analyst · spec · done
2026-10-05T13:45:55Z

**Did:** Wrote spec.md from gh:9: core → packs (labelled blocks) → local; docs policy; 0.2.0.

**Evidence:**
- read render_instructions (interleaves by filename, core wins ties) and its tests

**Changed files:** `specs/009-rule-precedence/spec.md`

**Open issues:** 7 criteria, 3 open questions with defaults

**Next:** Spec gate

## analyst · spec (revision 1) · done
2026-10-05T13:52:52Z

**Did:** Per the user at the Spec gate: added AC7 (validate fails when the newest CHANGELOG heading isn't VERSION, or an Unreleased heading exists); AC6 now writes 0.2.0 directly.

**Evidence:**
- spec reread; 8 criteria

**Changed files:** `specs/009-rule-precedence/spec.md`

**Open issues:** same 3 open questions with defaults

**Next:** Spec gate

## architect · plan · done
2026-10-05T14:30:26Z

**Did:** Wrote plan.md: render_instructions walks sources in order with comment+sentence labels; _check_changelog in cmd_validate; test helper writes VERSION+CHANGELOG together.

**Evidence:**
- read render_instructions, cmd_validate, test fixtures that write VERSION

**Changed files:** `specs/009-rule-precedence/plan.md`

**Open issues:** 4 tasks; callouts: 0.2.0 contract change, new validate rule for every PR, conflict with #30 expected

**Next:** Plan gate

## test-writer · T1 · done
2026-10-05T15:20:16Z

**Did:** RenderInstructionsTest: core-only render byte-identical (guard), pack 15-acme.md after every core rule, labelled pack blocks in source order (acme then beta), local rules last under a label sorted by filename.

**Evidence:**
- `python3 -m unittest tests.test_aicfg.RenderInstructionsTest` → 1 failure (interleaving assertion), 2 errors (label substring not found: missing behavior); core-only guard passes

**Changed files:** `tests/test_aicfg.py`

**Open issues:** none

**Next:** review T1

## code-reviewer · T1 · done
2026-10-05T15:20:16Z

**Did:** Reviewed T1 tests against AC1–AC4.

**Evidence:**
- last core rule read from the real rules dir at runtime, so adding a core rule won't break the tests

**Changed files:** none

**Findings:** none

**Open issues:** none

**Next:** commit T1, then T2

## implementer · T2 · done
2026-10-05T15:20:45Z

**Did:** render_instructions walks sources in order: core unlabelled, each pack under "<!-- pack: name -->" + one sentence, then local rules under "<!-- local -->". Filename order within each group.

**Evidence:**
- RenderInstructionsTest → OK; full suite → 51 OK; validate → OK

**Changed files:** `scripts/aicfg.py`

**Open issues:** none

**Next:** review T2

## code-reviewer · T2 · done
2026-10-05T15:20:45Z

**Did:** Reviewed T2 diff against AC1–AC4.

**Evidence:**
- pack with only local rules gets no empty pack label; README.md and *.local.md still excluded from shared rules; core-only output unchanged (guard test)

**Changed files:** none

**Findings:** none

**Open issues:** none

**Next:** commit T2, then T3

## implementer · T3 · done
2026-10-05T15:21:42Z

**Did:** check_changelog(core) in cmd_validate: errors on an Unreleased heading, a missing X.Y.Z heading, or newest heading != VERSION. Tests: ChangelogCheckTest; copy_repo copies CHANGELOG.md; set_core_version writes VERSION + matching CHANGELOG for pack tests.

**Evidence:**
- red: 3 assertion failures before the code
- ChangelogCheckTest OK; full suite 55 OK; validate OK; example pack OK

**Changed files:** `scripts/aicfg.py`, `tests/test_aicfg.py`

**Open issues:** none

**Next:** T4

## implementer · T4 · done
2026-10-05T15:22:12Z

**Did:** docs/formats.md and docs/packs.md (new Rules section) state the order and refine-don't-contradict policy; example pack and docs pin >=0.2, <0.3; VERSION 0.2.0; CHANGELOG 0.2.0 entry tagged [pack contract].

**Evidence:**
- old pin at 0.2.0 → ExamplePackTest fails naming requires_core (reverted); suite 55 OK; validate OK; example OK

**Changed files:** `docs/formats.md`, `docs/packs.md`, `examples/pack-acme/pack.toml`, `VERSION`, `CHANGELOG.md`

**Open issues:** none

**Next:** batched review (T3, T4)

## code-reviewer · batch (T3, T4) · done
2026-10-05T15:23:14Z

**Did:** Reviewed 8402b57..4d01a90 against AC5–AC8.

**Evidence:**
- pre-release headings (## 0.2.0-rc) still parse; pack CI clones core main, which always passes

**Changed files:** none

**Findings:** none

**Open issues:** none

**Next:** verify

## verifier + doc-writer · verify, document · done
2026-10-05T15:23:14Z

**Did:** Mapped AC1–AC8 in verify.md; manual apply showed core → acme block → local; core-only render equals main's. Drafted pr-body.md and ticket-comment.md.

**Evidence:**
- tests 55 OK; validate OK; example OK; sandbox OK

**Changed files:** `specs/009-rule-precedence/verify.md`, `specs/009-rule-precedence/pr-body.md`, `specs/009-rule-precedence/ticket-comment.md`

**Open issues:** merge order with #30

**Next:** Deliver gate
