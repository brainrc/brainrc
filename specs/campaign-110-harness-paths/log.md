# Campaign gh:110 log

## 2026-11-11T04:02:11Z · intake
- Members: gh:131 (closed, the seed), gh:132, gh:133, gh:134. All open members unassigned; none skipped.
- Shape: playbook (the epic says so; the three members share one template and differ in parameters).
- Shared context: gh:131's resolver (`_xdg_home`: absolute only, empty ignored) and spec 206-brainrc-settings-home.
- Auto run as the build plan asks: gates are logged and auto-approved, one draft PR for the epic.

## 2026-11-11T04:20:00Z · Campaign gate · auto-approved
Parameter table and playbook v1 as in `playbook.md`. Size: standard per member. One batch of 3.
Delivery: one branch and one draft PR to main for the whole epic (build plan), commits per member.

## 2026-11-11T04:55:00Z · batch 1 verified
- gh:132 seeded the resolver; gh:133 was harnesses.toml lines only; gh:134 added the opencode.jsonc merge
  (deviation within the playbook: an extra file, `brainrc/jsonc.py`).
- Finding: suites that fake HOME inherited XDG_CONFIG_HOME, CLAUDE_CONFIG_DIR and CODEX_HOME, so with the
  vars set they wrote into the real dirs. Fixed in gh:132's commit; the playbook's step 4 now says so.
- Finding: the manifest check trusted only paths inside `~`, so CLAUDE_CONFIG_DIR outside `~` made
  uninstall warn. It now also trusts the dir a harness var names now; the format is unchanged.

## 2026-11-11T05:10:04Z · Deliver gate · auto-approved
- gh:132, gh:133, gh:134 → draft PR #335 (base main), one commit each. Next: review by the owner's code-reviewer, then the owner merges.
