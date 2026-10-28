#!/usr/bin/env python3
"""Smoke-test an installed brainrc wheel (CI runs it after `pip install .`).

Run it from a directory outside the checkout, with the install's bin dir on PATH:
  cd "$RUNNER_TEMP" && python3 "$GITHUB_WORKSPACE/scripts/check_install.py"
Prints one PASS/FAIL line per check; exits 1 on any FAIL, 2 if brainrc isn't the installed copy.
The `brainrc` and `aicfg` on PATH must live in this interpreter's scripts dir.
"""
import importlib
import importlib.metadata as md
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# scripts/brainrc.py would shadow the package; drop this directory from the import path.
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]
EXPECTED_SCRIPTS = {"brainrc": "brainrc.cli:entry", "aicfg": "brainrc.cli:deprecated_entry"}
failed = False


def report(name: str, ok: bool, detail: str = "") -> None:
    global failed
    failed = failed or not ok
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))


def run(args: list[str], env: dict[str, str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, env=env, cwd=cwd, capture_output=True, text=True, timeout=120)


def lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def deprecation_lines(text: str) -> list[str]:
    return [line for line in lines(text) if "deprecated" in line]


def one_warning(text: str) -> bool:
    from brainrc.cli import SHIM_REMOVED_IN
    err = lines(text)
    return len(err) == 1 and "brainrc" in err[0] and SHIM_REMOVED_IN in err[0]


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

    new, old = sh("brainrc", "status"), sh("aicfg", "status")
    report("AC3 aicfg status == brainrc status",
           new.returncode == 0 and bool(new.stdout.strip()) and not deprecation_lines(new.stderr)
           and (old.stdout, old.returncode) == (new.stdout, new.returncode) and one_warning(old.stderr),
           f"exit aicfg {old.returncode} vs brainrc {new.returncode}; brainrc stdout empty: {not new.stdout.strip()}; "
           f"brainrc stderr {new.stderr!r}; aicfg stderr {old.stderr!r}")

    a = run([py, "-m", "brainrc", "status"], env, work)
    b = run([py, "-m", "aicfg", "status"], env, work)
    report("AC6 python -m brainrc / -m aicfg status and warnings",
           a.returncode == b.returncode and a.returncode == new.returncode and bool(a.stdout.strip())
           and a.stdout == b.stdout and not deprecation_lines(a.stderr) and one_warning(b.stderr),
           f"exit {a.returncode} vs {b.returncode}; brainrc stderr {a.stderr!r}; aicfg stderr {b.stderr!r}")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sys.modules.pop("aicfg", None)
        sys.modules.pop("aicfg.cli", None)
        aicfg = importlib.import_module("aicfg")
        import aicfg.cli
        import brainrc.cli
        ok = (any(issubclass(w.category, DeprecationWarning) and "aicfg" in str(w.message) for w in caught)
              and aicfg.cli.main is brainrc.cli.main
              and not Path(aicfg.__file__).resolve().is_relative_to(REPO))
    report("AC7 import aicfg warns and aliases brainrc.cli", ok,
           f"warnings {[str(w.message) for w in caught]}, aicfg at {aicfg.__file__}")


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
        env = {**os.environ, "HOME": str(home), "AICFG_HOME": str(home / "ai-config"), "USERPROFILE": str(home)}
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
