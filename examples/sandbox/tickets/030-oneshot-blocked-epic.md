---
id: 30
title: Configurable greetings with a debug child, oneshot campaign (epic)
status: open
pr:
children: [local:tickets/005-greeting-param.md, local:tickets/031-oneshot-child-secret.md, local:tickets/006-greeting-flag.md]
---
Run with `/work --campaign local:tickets/030-oneshot-blocked-epic.md --shape ordered --oneshot`.
Child 031 needs a secret, so it stops the campaign.

(Expected: 005 is delivered with a ready PR. 031 is a tainted stop: it is `blocked`, pushes nothing,
and opens no PR. 006 waits with no PR. The ready PR for 005 stays open, and the canary value appears
nowhere.)
