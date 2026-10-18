---
id: 3
title: Add a farewell command and a --version flag
status: open
pr:
---
Two small, independent additions:

1. A new `farewell.py` that prints `Goodbye, <name>!` (default name `world`), with its own tests.
2. A `--version` flag on `greet.py` that prints `greet 1.0` and exits.

They touch different files, so in subagent mode spec-agent should run them as one parallel
wave. The change is small enough to size `small`, which runs inline; the wave needs
`resize standard` at the Spec gate. Without either flag, `greet.py`'s output must not change.
