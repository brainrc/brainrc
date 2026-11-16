#!/usr/bin/env python3
"""Time each install route from scratch to the first `brainrc status` (E26's 60-second target).

Usage: python3 scripts/check_install_time.py [--path uvx|pipx|npx|brew ...] [--limit SECONDS]
                                            [--local DIST_DIR | --published]
Each route runs in a fresh temp HOME (empty uv, pip, npm and pipx caches; ~/.claude present, as for
a Claude Code user), and the clock runs from the install command to the end of the first `status`.
--local installs what this checkout builds: the wheel and sdist in DIST_DIR (`python3 -m build`),
the repo packed with `npm pack`, and a formula for the local sdist in a scratch tap; uv and pip are
kept offline, but for the pip that pipx fetches for itself. --published (the default) installs what
users get: PyPI, `npx github:brainrc/brainrc` and the brainrc/homebrew-tap tap. A route whose tool
or source is missing (no brew on the machine, no PyPI release yet, the repo not public, no tap)
prints SKIP, never PASS. A route over its limit is SLOW: a FAIL, but for brew, whose time is
mostly Homebrew installing Python and swings with the runner, a WARN that doesn't fail the run.
Exits 1 on any FAIL. Under GitHub Actions a WARN is also a ::warning:: annotation, and every
route's result goes to the step summary.
Homebrew runs with HOMEBREW_NO_AUTO_UPDATE and its own download cache, so `brew update` and its
API data aren't counted; brew skips when brainrc is already installed with Homebrew, and uninstalls
what it installed afterwards.
"""
import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Loaded by path: scripts/ on sys.path would let scripts/brainrc.py hide the brainrc package.
_spec = importlib.util.spec_from_file_location("homebrew_formula", REPO / "scripts" / "homebrew_formula.py")
homebrew_formula = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(homebrew_formula)
render, sha256_of, version_of = homebrew_formula.render, homebrew_formula.sha256_of, homebrew_formula.version_of

PATHS = ("uvx", "pipx", "npx", "brew")
VERSION = (REPO / "VERSION").read_text().strip()
ENV_DROP = ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_BIN_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME",
            "UV_TOOL_DIR", "UV_TOOL_BIN_DIR", "UV_CACHE_DIR", "PIPX_HOME", "PIPX_BIN_DIR",
            "npm_config_cache", "NPM_CONFIG_CACHE", "CLAUDE_CONFIG_DIR", "PYTHONPATH", "BRAINRC_HOME")
STATUS_OK = "Dry run. Run `apply` to write."
LOCAL_TAP = "brainrc-check/local"


class Skip(Exception):
    pass


def find_brew() -> str | None:
    found = shutil.which("brew")
    for p in (found, "/opt/homebrew/bin/brew", "/usr/local/bin/brew", "/home/linuxbrew/.linuxbrew/bin/brew"):
        if p and Path(p).is_file():
            return p
    return None


def quiet(args: list[str], env: dict | None = None, timeout: int = 60, cwd: Path | None = None) -> bool:
    try:
        return subprocess.run(args, env=env, cwd=cwd, capture_output=True, timeout=timeout).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def need(tool: str) -> str:
    found = shutil.which(tool)
    if not found:
        raise Skip(f"{tool} not installed")
    return found


def public(url: str, work: Path) -> bool:
    """Whether anyone can read the repo: git without the caller's config or credentials (CI's
    checkout leaves a token in its own .git/config, so run outside it)."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    return quiet(["git", "-c", "credential.helper=", "ls-remote", url, "HEAD"], env=env, cwd=work)


def on_pypi(version: str | None = None) -> None:
    """Skip unless PyPI has brainrc (at `version`, if given). A pip that can't answer is an error,
    not a skip, so a broken check can't stay green."""
    args = [sys.executable, "-m", "pip", "index", "versions", "brainrc"]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"couldn't ask PyPI: {e}") from None
    if r.returncode == 0 and (version is None or re.search(rf"[ ,]{re.escape(version)}(,|$)", r.stdout, re.M)):
        return
    if r.returncode == 0 or "No matching distribution" in r.stderr:
        raise Skip(f"brainrc {version} is not on PyPI yet" if version else "brainrc is not on PyPI yet")
    raise RuntimeError(f"couldn't ask PyPI: {(r.stderr or r.stdout)[-300:]}")


def local_env(dist: Path) -> dict[str, str]:
    d = str(dist.resolve())
    return {"UV_FIND_LINKS": d, "UV_OFFLINE": "1", "PIP_FIND_LINKS": d, "PIP_NO_INDEX": "1"}


def plan(route: str, local: Path | None, work: Path) -> tuple[str, dict[str, str], list[str]]:
    """(bash script that installs and runs the first status, extra environment, directories to put
    first on PATH); Skip if impossible."""
    extra = local_env(local) if local else {}
    if route == "uvx":
        need("uvx")
        if not local:
            on_pypi()
        return "uvx brainrc status", extra, []
    if route == "pipx":
        need("pipx")
        if not local:
            on_pypi()
            return "pipx install brainrc\nbrainrc status", extra, []
        # pipx's first run fetches pip for its shared environment from the index, as it does for a
        # new user, so this route can't be offline: it installs the local wheel by its path.
        wheel = local / f"brainrc-{VERSION}-py3-none-any.whl"
        if not wheel.is_file():
            raise RuntimeError(f"{wheel} missing: build it with python3 -m build")
        return f"pipx install '{wheel.resolve()}'\nbrainrc status", {}, []
    if route == "npx":
        need("npx")
        need("uvx")  # the shim runs brainrc through uvx
        if local:
            npm = need("npm")
            r = subprocess.run([npm, "pack", "--pack-destination", str(work)], cwd=REPO,
                               capture_output=True, text=True, timeout=120)
            tgz = work / f"brainrc-{VERSION}.tgz"
            if r.returncode or not tgz.is_file():
                raise RuntimeError(f"npm pack failed: {r.stderr[-400:]}")
            return f"npx --yes --package '{tgz}' brainrc status", extra, []
        if not public("https://github.com/brainrc/brainrc", work):
            raise Skip("github.com/brainrc/brainrc is not public")
        on_pypi(VERSION)  # the shim pins the repo's VERSION
        return "npx --yes github:brainrc/brainrc status", extra, []
    if route == "brew":
        brew = find_brew()
        if not brew:
            raise Skip("Homebrew not installed")
        if quiet([brew, "list", "--formula", "brainrc"]):
            raise Skip("brainrc is already installed with Homebrew; `brew uninstall brainrc` to time this route")
        # Homebrew builds the sdist itself and fetches the build backend from PyPI: no offline pip.
        # Its download cache stays the machine's, as a Homebrew user's would.
        extra = {"HOMEBREW_NO_AUTO_UPDATE": "1", "HOMEBREW_NO_INSTALL_CLEANUP": "1", "HOMEBREW_NO_ENV_HINTS": "1"}
        try:
            cache = subprocess.run([brew, "--cache"], capture_output=True, text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            cache = ""
        if cache:
            extra["HOMEBREW_CACHE"] = cache
        if local:
            sdist = local / f"brainrc-{VERSION}.tar.gz"
            if not sdist.is_file():
                raise RuntimeError(f"{sdist} missing: build it with python3 -m build")
            (local_tap(brew) / "Formula" / "brainrc.rb").write_text(local_formula(sdist))
            return f"brew install {LOCAL_TAP}/brainrc\nbrainrc status", extra, [str(Path(brew).parent)]
        if not public("https://github.com/brainrc/homebrew-tap", work):
            raise Skip("the brainrc/homebrew-tap tap doesn't exist yet")
        return "brew install brainrc/tap/brainrc\nbrainrc status", extra, [str(Path(brew).parent)]
    raise ValueError(route)


def local_formula(sdist: Path) -> str:
    """The release formula, with the sdist's URL replaced by the local file's."""
    https = render(version_of(sdist), f"https://local.invalid/{sdist.name}", sha256_of(sdist))
    return https.replace(f'url "https://local.invalid/{sdist.name}"', f'url "{sdist.resolve().as_uri()}"')


def local_tap(brew: str) -> Path:
    """A scratch tap for the local formula (Homebrew installs formulae only from taps), made as
    release.yml makes its own: `brew tap-new --no-git`."""
    env = {**os.environ, "HOMEBREW_NO_AUTO_UPDATE": "1"}
    quiet([brew, "untap", "--force", LOCAL_TAP], env=env, timeout=120)
    subprocess.run([brew, "tap-new", "--no-git", LOCAL_TAP], env=env, capture_output=True, check=True, timeout=120)
    repo = subprocess.run([brew, "--repository", LOCAL_TAP], env=env, capture_output=True, text=True,
                          check=True, timeout=60).stdout.strip()
    (Path(repo) / "Formula").mkdir(parents=True, exist_ok=True)
    return Path(repo)


def run_route(route: str, local: Path | None, limit: float) -> tuple[str, str]:
    """('PASS'|'SLOW'|'FAIL'|'SKIP', detail): SLOW installed and ran, but over the limit."""
    work = Path(tempfile.mkdtemp(prefix=f"install-time-{route}-"))
    planned = False
    try:
        try:
            script, extra, prepend = plan(route, local, work)
        except Skip as e:
            return "SKIP", str(e)
        planned = True
        home = work / "home"
        (home / ".claude").mkdir(parents=True)
        env = {k: v for k, v in os.environ.items() if k not in ENV_DROP}
        env.update(extra, HOME=str(home), USERPROFILE=str(home),
                   PATH=os.pathsep.join([str(home / ".local" / "bin"), *prepend, env.get("PATH", "")]))
        start = time.monotonic()
        try:
            r = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script], cwd=home, env=env,
                               capture_output=True, text=True, timeout=max(limit * 5, 300))
        except subprocess.TimeoutExpired:
            return "FAIL", f"still running after {max(limit * 5, 300):.0f} s"
        took = time.monotonic() - start
        if r.returncode or STATUS_OK not in r.stdout:
            tail = (r.stdout + r.stderr)[-800:]
            return "FAIL", f"exit {r.returncode} after {took:.1f} s\n{tail}"
        if took > limit:
            return "SLOW", f"{took:.1f} s to first status, over the {limit:.0f} s limit"
        return "PASS", f"{took:.1f} s to first status"
    finally:
        brew = find_brew() if route == "brew" and planned else None
        if brew:  # plan skipped when brainrc was installed before, so this is the check's own
            quiet([brew, "uninstall", "--formula", "brainrc"], timeout=120)
            if local:
                quiet([brew, "untap", "--force", LOCAL_TAP], timeout=120)
        shutil.rmtree(work, ignore_errors=True)


# Seconds allowed per route. Homebrew installs python@3.13 and builds a virtualenv, and lands near
# 60 s on CI runners, so the maintainer set its limit to 90 s (2026-11-15).
LIMITS = {"uvx": 60.0, "pipx": 60.0, "npx": 60.0, "brew": 90.0}
# Routes whose limit warns instead of failing. Brew still ran 90-99 s on some runners after the
# raise, from runner speed rather than brainrc (the other routes take seconds), so a slow brew run
# warns; a brew install that breaks still fails (2026-11-16).
WARN_ONLY = {"brew"}


def report(result: str, route: str, detail: str) -> None:
    """Print the route's line; under GitHub Actions, annotate a WARN and add a step summary line."""
    print(f"{result} {route}: {detail}", flush=True)
    first = detail.splitlines()[0] if detail else ""
    if result == "WARN" and os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title=install-time {route}::{first.replace('%', '%25')}", flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as f:
                f.write(f"- {result} {route}: {first}\n")
        except OSError:
            pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--path", action="append", choices=PATHS, help="route to time (repeatable; default all)")
    ap.add_argument("--limit", type=float, help="seconds allowed to first status, for every route "
                    "(default: 60, 90 for brew)")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--local", type=Path, metavar="DIST_DIR", help="install this checkout's build")
    src.add_argument("--published", action="store_true", help="install the published releases (default)")
    args = ap.parse_args(argv)
    failed = False
    for route in args.path or PATHS:
        try:
            limit = args.limit if args.limit is not None else LIMITS[route]
            result, detail = run_route(route, args.local, limit)
        except Exception as e:  # a crash is a FAIL line, never a traceback
            result, detail = "FAIL", f"{type(e).__name__}: {e}"
        if result == "SLOW":
            result = "WARN" if route in WARN_ONLY else "FAIL"
        report(result, route, detail)
        failed = failed or result == "FAIL"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
