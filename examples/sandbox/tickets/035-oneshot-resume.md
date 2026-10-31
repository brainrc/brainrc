---
id: 35
title: Print the greeting in capitals (oneshot run, resumed)
status: open
pr:
---
Start with `/work local:tickets/035-oneshot-resume.md --oneshot` and interrupt the run once the Spec
gate is auto-approved. Then resume with `/work local:tickets/035-oneshot-resume.md` and no flag. Add
a `--caps` flag that prints the greeting in capitals.

(Expected: resume clears `oneshot` and `auto`. The Plan gate is not auto-approved: it stays pending
until you approve it.)
