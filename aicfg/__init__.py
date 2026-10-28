"""Deprecated: `aicfg` is now `brainrc`. This shim is removed in brainrc.cli.SHIM_REMOVED_IN."""
import sys
import warnings

import brainrc.cli as cli

# `python -m aicfg` imports this package first, then aicfg/__main__.py prints its own warning.
if not (sys.argv[:1] == ["-m"] and "aicfg" in sys.orig_argv):
    warnings.warn(f"aicfg is deprecated: import brainrc instead (removed in {cli.SHIM_REMOVED_IN})",
                  DeprecationWarning, stacklevel=2)

sys.modules["aicfg.cli"] = cli
