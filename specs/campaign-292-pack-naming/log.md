# Campaign gh:292 log

## 2026-11-11T06:40:00Z · intake
- Members, in epic order: gh:293 (document the rules), gh:294 (validate enforces them), gh:295 (core agents
  under `brainrc-`). All open and unassigned; none skipped.
- Shape: the epic says "independent", which spec-agent doesn't have. The children differ and carry no
  links, so this runs as `ordered` with `dependency_source: none` (epic order).
- The issues name the roadmap's "official pack ID table", which isn't in this repo. The table is built
  from the open "Official pack" issues (#313 to #317, #323), the only `brainrc/<pack>` IDs on record.
- Auto run as the owner asked ("use spec-agent flow campaign to complete the epic"): gates are logged
  and auto-approved, one branch and one draft PR to main for the epic, one commit per member.

## 2026-11-11T06:45:00Z · Campaign gate · auto-approved
Order gh:293 → gh:294 → gh:295. Size standard each. Delivery: one draft PR, `Closes` per member.

## 2026-11-11T07:35:00Z · all members verified
- gh:293 docs, gh:294 `brainrc/naming.py` with near-miss tests, gh:295 agents renamed with aliases.
- The naming checks are a breaking [pack contract] change, so the fragment says `bump: minor` (0.6.0), and
  the agent aliases go in 0.7.0. 0.6.0 is also the release the five skill aliases from 0.5.14 promised to
  leave in; removing them is outside this epic, so they stay. Owner's call whether to remove them first.
- The example packs now pin `<0.7` so they still validate after the release.
