Done in the linked PR (0.3.7). `python3 scripts/aicfg.py doctor` is read-only and covers every item in the proposal. Two choices worth knowing about:
- A harness that isn't installed is a WARN, not a FAIL, because `harnesses.toml` enables all five by default.
- The Python version check is an import guard that covers every command, since `aicfg.py` couldn't start on 3.10 at all.
