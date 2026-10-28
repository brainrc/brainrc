#!/usr/bin/env python3
"""brainrc from a checkout: `python3 scripts/brainrc.py <command>` (run with no command for usage).

The code is the `brainrc` package at the repo root; this script runs it without installing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brainrc.cli import main  # noqa: E402  (needs the repo root on sys.path first)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
