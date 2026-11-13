#!/usr/bin/env python3
"""Run local tripwires in CI (#344): the terms come from the TRIPWIRE_TERMS secret, one per line.

validate.yml's `tripwires` job runs it with these environment variables:
  TRIPWIRE_TERMS  the secret; empty when it isn't set, or for a PR that can't read secrets
  NO_SECRETS      "true" for a fork or Dependabot PR: skip with a notice, the push to main checks it
Each term is masked in the log, written to a terms file in $RUNNER_TEMP (never the checkout), and
`validate --local-tripwires` checks every tracked core file, naming a match's file, line and term
number but never the term. Exits 0 when clean or skipped, 1 on a match or when the secret is unset.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SECRET = "TRIPWIRE_TERMS"


def toml_string(s: str) -> str:
    """s as a TOML basic string: quotes, backslashes and control characters escaped."""
    out = []
    for ch in s:
        if ch in '"\\':
            out.append("\\" + ch)
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def mask(term: str) -> None:
    """GitHub masks exact text only; validate matches any case, so mask the usual spellings too."""
    for variant in sorted({term, term.lower(), term.upper(), term.title(), term.casefold()}):
        print(f"::add-mask::{variant}", flush=True)


def main() -> int:
    if os.environ.get("NO_SECRETS") == "true":
        print(f"::notice::Local tripwires skipped: this PR can't read the {SECRET} secret. "
              "The push to main runs them.")
        return 0
    terms = [t.strip() for t in os.environ.get(SECRET, "").splitlines() if t.strip()]
    if not terms:
        print(f"::error::Local tripwire terms are not configured: set the {SECRET} repository secret, "
              "one term per line.")
        return 1
    for t in terms:
        mask(t)
    tmp = Path(tempfile.mkdtemp(dir=os.environ.get("RUNNER_TEMP")))
    path = tmp / "tripwires.local.toml"
    try:
        path.write_text("terms = [" + ", ".join(toml_string(t) for t in terms) + "]\n")
        env = {**os.environ, "GITHUB_ACTIONS": "true"}  # validate redacts terms from its output
        env.pop(SECRET)
        cmd = [sys.executable, str(REPO / "scripts/brainrc.py"), "validate", "--local-tripwires", str(path)]
        return subprocess.run(cmd, env=env).returncode
    finally:
        path.unlink(missing_ok=True)
        tmp.rmdir()


if __name__ == "__main__":
    sys.exit(main())
