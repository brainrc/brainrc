## analyst · spec · done
2026-10-08T03:19:27Z

**Did:** Spec (standard) from a real Codex 0.161.0 install (scratch prefix and CODEX_HOME) and the Claude Code skills docs.

**Evidence:**
- codex plugin marketplace add + plugin add: installed 0.3.16, enabled
- installed copy: roles symlink missing; no work/review/spec-* skills; no hooks evidence
- claude-code-guide: skills invoked as /name, $ARGUMENTS works, skill beats command

**Changed files:** `specs/050-codex/spec.md`

**Open issues:** Codex hooks unverified (needs login)

**Next:** Spec gate

## planner · plan · done
2026-10-08T03:24:26Z

**Did:** 5 tasks; red test first (core commands/ exists today).

**Evidence:**
- spec approved 2026-10-08T03:24:26Z (recorded right after the click)

**Changed files:** `specs/050-codex/plan.md`

**Open issues:** none

**Next:** Plan gate

## implementer + verifier + doc-writer · T1–T5, verify, document · done
2026-10-08T03:28:16Z

**Did:** Commands to skills with the shape test (717b1a6), roles fallback (361ddb5), docs and 0.3.17 (c9f3209).

**Evidence:**
- red: test_core_has_no_commands_folder failed while commands/ existed
- real apply upgrade in a fake HOME; real Codex reinstall shows the 5 skills
- tests OK; validate OK; claude plugin validate OK; tutorial ran clean

**Changed files:** see the PR diff stat

**Open issues:** Codex hooks and rules unverified (login needed)

**Next:** Deliver gate
