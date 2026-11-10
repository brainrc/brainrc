#!/usr/bin/env python3
"""Smoke-test an installed brainrc wheel (CI runs it after `pip install .`).

Run it from a directory outside the checkout, with the install's bin dir on PATH:
  cd "$RUNNER_TEMP" && python3 "$GITHUB_WORKSPACE/scripts/check_install.py"
Prints one PASS/FAIL line per check; exits 1 on any FAIL, 2 if brainrc isn't the installed copy.
The `brainrc` on PATH must live in this interpreter's scripts dir.
"""
import importlib.metadata as md
import importlib.util
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# scripts/brainrc.py would shadow the package; drop this directory from the import path.
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]
EXPECTED_SCRIPTS = {"brainrc": "brainrc.cli:entry"}
failed = False


def report(name: str, ok: bool, detail: str = "") -> None:
    global failed
    failed = failed or not ok
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))


def run(args: list[str], env: dict[str, str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, env=env, cwd=cwd, capture_output=True, text=True, timeout=120)


def lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def checks(work: str, env: dict[str, str], scripts: dict[str, str]) -> None:
    import brainrc
    py = sys.executable

    def sh(name: str, *args: str) -> subprocess.CompletedProcess:
        return run([scripts[name], *args], env, work)

    try:
        dist = md.distribution("brainrc")
        found = {e.name: e.value for e in dist.entry_points if e.group == "console_scripts"}
        report("AC2 console_scripts", found == EXPECTED_SCRIPTS, f"got {found}")
        version = dist.version
    except md.PackageNotFoundError:
        report("AC2 console_scripts", False, "distribution brainrc not found")
        version = ""

    r = sh("brainrc", "--version")
    report("AC1 brainrc --version", r.returncode == 0 and r.stdout.strip() == f"brainrc {version}",
           f"exit {r.returncode}, stdout {r.stdout!r}, expected 'brainrc {version}'")

    core = Path(brainrc.__file__).parent / "_core"
    needed = ["skills", "agents", "rules", "harnesses.toml", "VERSION", "CHANGELOG.md"]
    absent = [n for n in needed if not (core / n).exists()]
    from brainrc import config
    r = sh("brainrc", "validate")
    report("AC8 brainrc validate outside a checkout, bundled _core",
           r.returncode == 0 and core.is_dir() and not absent and config.installed(),
           f"exit {r.returncode}; _core dir {core.is_dir()}, missing {absent}, installed() {config.installed()}\n"
           f"{r.stdout[-500:]}{r.stderr[-500:]}")

    new = sh("brainrc", "status")
    report("AC3 brainrc status",
           new.returncode == 0 and bool(new.stdout.strip()) and not new.stderr.strip(),
           f"exit {new.returncode}; stdout empty: {not new.stdout.strip()}; stderr {new.stderr!r}")

    a = run([py, "-m", "brainrc", "status"], env, work)
    report("AC6 python -m brainrc status matches the script",
           (a.returncode, a.stdout) == (new.returncode, new.stdout) and not a.stderr.strip(),
           f"exit {a.returncode} vs {new.returncode}; stderr {a.stderr!r}")

    gone = importlib.util.find_spec("aicfg") is None
    report("AC1 no aicfg package installed", gone)


def main() -> int:
    try:
        import brainrc
    except ImportError:
        print("REFUSE brainrc is not importable; use the python of the environment it was installed into")
        return 2
    if Path(brainrc.__file__).resolve().is_relative_to(REPO):
        print(f"REFUSE brainrc resolves inside the checkout ({brainrc.__file__}); "
              "test the installed copy: cd outside the repo and use the install's python")
        return 2

    bindir = Path(sysconfig.get_path("scripts")).resolve()
    scripts = {n: shutil.which(n) for n in EXPECTED_SCRIPTS}
    missing = [n for n, p in scripts.items() if not p]
    if missing:
        print(f"REFUSE {', '.join(missing)} not on PATH; put the install's bin dir first")
        return 2
    stray = [f"{n} -> {p}" for n, p in scripts.items() if Path(p).parent.resolve() != bindir]
    if stray:
        print(f"REFUSE not from this interpreter's scripts dir {bindir}: {'; '.join(stray)}")
        return 2

    work = tempfile.mkdtemp(prefix="check-install-")
    try:
        home = Path(work, "home")
        home.mkdir()
        env = {**os.environ, "HOME": str(home), "BRAINRC_HOME": str(home / "brainrc"), "USERPROFILE": str(home)}
        env.pop("PYTHONWARNINGS", None)
        env.pop("PYTHONPATH", None)
        checks(work, env, scripts)
    except Exception as e:  # a crash is a FAIL line, never a traceback
        report("check_install", False, f"{type(e).__name__}: {e}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
