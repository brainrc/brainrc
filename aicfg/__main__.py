"""Deprecated `python -m aicfg`: warn, then run brainrc."""
import sys

from brainrc.cli import main, warn_deprecated

warn_deprecated("python -m aicfg", "python -m brainrc")
sys.exit(main(sys.argv))
