---
id: 12
title: Greetings in more languages (auto run)
status: open
pr:
---
Run with `--auto`. Add a `--lang` option (`en`, `fr`, `de`; default `en`) that picks the greeting
word ("Hello", "Bonjour", "Hallo"). Keep the words in a new `greetings.py` table so more languages
are one line each, add tests, and document the option in a new `README.md` "Usage" section.
An unknown language exits 2 with a message listing the supported ones. Without the option,
output must not change.

(Expected: sizes `standard`, runs with no gate stop, logs the Spec, Plan, and Deliver gates as
`auto-approved`.)
