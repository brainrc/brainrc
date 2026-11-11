#!/usr/bin/env python3
"""Run the commands of docs/tutorial.md (steps 1-5) in a temporary HOME and checkout copy.

Usage: python3 scripts/check_tutorial.py [--doc PATH]
The commands are read from the doc, so a changed command is run as changed. Step 1's `git clone`
line is replaced by a copy of this checkout at <tmp>/home/brainrc (the tutorial's ~/brainrc), so
the real checkout and HOME are never written. Prints one PASS/FAIL line per step; exits 1 on any FAIL.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STEPS = (1, 2, 3, 4, 5)
# Documented output each step must print, besides exiting 0.
EXPECTED = {
    1: [r"(?m)^OK:"],
    4: [r"(?m)^OK:", re.escape("(packs: myteam)")],
    5: [re.escape("Everything in sync.")],
}
COPY_IGNORE = shutil.ignore_patterns(".git", "dist", "__pycache__", "*.local.*", ".env*")
HEADING = re.compile(r"^## (\d+)\. (.+?)\s*$")
FENCE = re.compile(r"^```bash\s*$")


def report(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))


def parse(text: str) -> dict[int, tuple[str, str]]:
    """Map step number -> (title, first bash block) for the steps we run; ValueError if any is absent."""
    found: dict[int, tuple[str, str]] = {}
    num = title = None
    block: list[str] | None = None
    for line in text.splitlines():
        if block is not None:
            if line.startswith("```"):
                found.setdefault(num, (title, "\n".join(block) + "\n"))
                block = None
            else:
                block.append(line)
            continue
        m = HEADING.match(line)
        if m:
            num, title = int(m.group(1)), m.group(2)
        elif num in STEPS and num not in found and FENCE.match(line):
            block = []
    missing = [n for n in STEPS if n not in found]
    if missing:
        raise ValueError(f"tutorial steps without a heading and bash block: {missing}")
    found = {n: found[n] for n in STEPS}
    title, block = found[1]
    found[1] = (title, "".join(l + "\n" for l in block.splitlines() if not l.startswith("git clone")))
    return found


def steps(text: str) -> dict[int, str]:
    return {n: block for n, (_, block) in parse(text).items()}


def tail(text: str, n: int = 800) -> str:
    return text[-n:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", default=str(REPO / "docs" / "tutorial.md"), help="tutorial to run")
    args = ap.parse_args(argv)
    failed = False
    work = tempfile.mkdtemp(prefix="check-tutorial-")
    try:
        parsed = parse(Path(args.doc).read_text(encoding="utf-8"))
        home = Path(work, "home")
        checkout = home / "brainrc"
        shutil.copytree(REPO, checkout, symlinks=True, ignore=COPY_IGNORE)
        (home / ".claude").mkdir()  # apply only touches installed harnesses, so install one
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home),
               "BRAINRC_HOME": str(home / ".config" / "brainrc")}
        for k in ("XDG_CONFIG_HOME", "PYTHONPATH"):
            env.pop(k, None)
        for n, (title, block) in parsed.items():
            name = f"step {n} {title}"
            try:
                r = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", block], cwd=checkout, env=env,
                                   capture_output=True, text=True, timeout=120)
            except subprocess.TimeoutExpired:
                report(name, False, "timed out after 120 s")
                failed = True
                break
            absent = [p for p in EXPECTED.get(n, []) if not re.search(p, r.stdout)]
            ok = r.returncode == 0 and not absent
            detail = (f"exit {r.returncode}" if r.returncode else f"output missing {absent}")
            report(name, ok, f"{detail}\n--- stdout\n{tail(r.stdout)}\n--- stderr\n{tail(r.stderr)}")
            if not ok:
                failed = True
                break  # later steps build on this one
    except Exception as e:  # a crash is a FAIL line, never a traceback
        report("check_tutorial", False, f"{type(e).__name__}: {e}")
        failed = True
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
