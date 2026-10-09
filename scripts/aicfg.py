#!/usr/bin/env python3
"""aicfg from a checkout: `python3 scripts/aicfg.py <command>` (run with no command for usage).

The code is the `aicfg` package at the repo root; this shim keeps the documented command working.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from aicfg.cli import main  # noqa: E402  (needs the repo root on sys.path first)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
