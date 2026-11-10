"""`python3 -m brainrc <command>`: the same commands as `python3 scripts/brainrc.py`."""
import sys

from .cli import main

sys.exit(main(sys.argv))
