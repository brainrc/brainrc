"""A pack's own tests (#138): pack.toml `test = "<dir or file>.py"` names unittest tests in the pack,
and `validate --pack` runs them. They are the pack's code, so only `validate --pack` from the command
line runs them (doctor and apply never do), in a fresh Python with brainrc importable, so they can
use brainrc.testing."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .sources import Source

TIMEOUT = 300  # seconds for the whole run
TAIL = 20  # lines of a failing run's output to show


def run(src: Source) -> list[str]:
    """Errors from running src's tests; none when it names none or they pass."""
    name = src.meta.get("test")
    if not isinstance(name, str) or not name:
        return []  # the pack.toml schema check reports a wrong type
    where = f"{src.name}:pack.toml: `test`"
    root = src.root.resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not (path.is_dir() or (path.is_file() and path.suffix == ".py")):
        return [f"{where} must name a directory or a .py file in the pack ({name})"]
    start, pattern = (path, "test*.py") if path.is_dir() else (path.parent, path.name)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PYTHONPATH=os.pathsep.join(filter(None, [str(Path(__file__).resolve().parent.parent),
                                                        os.environ.get("PYTHONPATH")])))
    try:
        done = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(start),
                               "-p", pattern], cwd=root, env=env, capture_output=True, text=True,
                              timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return [f"{where}: {name} took over {TIMEOUT}s, so validate stopped it"]
    out = (done.stderr + done.stdout).strip()
    if "\nRan 0 tests" in "\n" + out:
        return [f"{where}: {name} has no tests (unittest found none matching {pattern})"]
    if done.returncode != 0:
        tail = "\n".join("    " + line for line in out.splitlines()[-TAIL:])
        return [f"{src.name}:{name}: the pack's tests failed:\n{tail}"]
    return []
