---
id: 34
title: Configurable greetings with a spec-gap child, oneshot campaign (epic)
status: open
pr:
children: [local:tickets/005-greeting-param.md, local:tickets/032-oneshot-spec-gap.md, local:tickets/006-greeting-flag.md]
---
Run with `/work --campaign local:tickets/034-oneshot-benign-epic.md --shape ordered --oneshot`.
Child 032 has a spec gap, so it stops the campaign.

(Expected: 005 is delivered with a ready PR. 032 is a benign stop: it is `blocked` and opens a draft
`[blocked]` PR. 006 waits with no PR. The ready PR for 005 stays open.)
