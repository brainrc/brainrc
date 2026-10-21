---
id: 6
title: Add a --greeting flag
status: open
pr:
depends_on: [local:tickets/005-greeting-param.md]
---
Add `--greeting WORD` to `greet.py`, passed to the `greeting` parameter of `greet()` added in
ticket 005. `python3 greet.py --greeting Hi Ada` prints `Hi, Ada!`.
