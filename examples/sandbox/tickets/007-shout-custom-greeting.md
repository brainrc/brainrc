---
id: 7
title: Add --shout that upper-cases the whole greeting
status: open
pr:
depends_on: [local:tickets/006-greeting-flag.md]
---
Add `--shout` to `greet.py`: it prints the greeting in upper case, including a custom one from
`--greeting` (ticket 006). `python3 greet.py --greeting Hi --shout Ada` prints `HI, ADA!`.
