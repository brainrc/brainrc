"""`python3 -m aicfg <command>`: the same commands as `python3 scripts/aicfg.py`."""
import sys

from .cli import main

sys.exit(main(sys.argv))
