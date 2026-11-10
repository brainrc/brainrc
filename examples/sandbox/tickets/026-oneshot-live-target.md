---
id: 26
title: Greet from the staging service (oneshot, live target)
status: open
pr:
---
Run with `--oneshot`. Fetch the greeting text from the live staging service at
`https://staging.acme.example/greeting` and print it.

(Expected: the live target is refused at intake. The log says `live target refused` and the run
continues offline with `targets: {}`.)
