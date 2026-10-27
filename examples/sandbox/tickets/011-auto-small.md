---
id: 11
title: Add --exclaim flag (auto run)
status: open
pr:
---
Run with `--auto`. Add an `--exclaim N` option that ends the greeting with N exclamation marks
instead of one (default 1). Without the option, output must not change.

(Expected: sizes `small`, runs with no gate stop, logs the Spec and Deliver gates as
`auto-approved`, and records the branch as its PR.)
