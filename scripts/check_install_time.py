#!/usr/bin/env python3
"""Time each install route from scratch to the first `brainrc status` (E26's 60-second target).

Usage: python3 scripts/check_install_time.py [--path uvx|pipx|npx|brew ...] [--limit 60]
                                            [--local DIST_DIR | --published]
Each route runs in a fresh temp HOME (empty uv, pip, npm and pipx caches; ~/.claude present, as for
a Claude Code user), and the clock runs from the install command to the end of the first `status`.
--local installs what this checkout builds: the wheel and sdist in DIST_DIR (`python3 -m build`),
the repo packed with `npm pack`, and a formula for the local sdist in a scratch tap; uv and pip are
kept offline. --published (the default) installs what users get: PyPI, `npx github:brainrc/brainrc`
and the brainrc/homebrew-tap tap. A route whose tool or source is missing (no brew on the machine,
no PyPI release yet, the repo not public, no tap) prints SKIP, never PASS. Exits 1 on any FAIL.
Homebrew runs with HOMEBREW_NO_AUTO_UPDATE, so `brew update` time isn't counted.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from homebrew_formula import render, sha256_of, version_of  # noqa: E402

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


def quiet(args: list[str], env: dict | None = None, timeout: int = 60) -> bool:
    try:
        return subprocess.run(args, env=env, capture_output=True, timeout=timeout).returncode == 0
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
    try:
        return subprocess.run(["git", "-c", "credential.helper=", "ls-remote", url, "HEAD"], cwd=work, env=env,
                              capture_output=True, timeout=60).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def local_env(dist: Path) -> dict[str, str]:
    d = str(dist.resolve())
    return {"UV_FIND_LINKS": d, "UV_OFFLINE": "1", "PIP_FIND_LINKS": d, "PIP_NO_INDEX": "1"}


def plan(route: str, local: Path | None, work: Path) -> tuple[str, dict[str, str]]:
    """(bash script that installs and runs the first status, extra environment); Skip if impossible."""
    extra = local_env(local) if local else {}
    if route == "uvx":
        need("uvx")
        if not local and not quiet([sys.executable, "-m", "pip", "index", "versions", "brainrc"]):
            raise Skip("brainrc is not on PyPI yet")
        return "uvx brainrc status", extra
    if route == "pipx":
        need("pipx")
        if not local and not quiet([sys.executable, "-m", "pip", "index", "versions", "brainrc"]):
            raise Skip("brainrc is not on PyPI yet")
        return "pipx install brainrc\nbrainrc status", extra
    if route == "npx":
        need("npx")
        if local:
            npm = need("npm")
            r = subprocess.run([npm, "pack", "--pack-destination", str(work)], cwd=REPO,
                               capture_output=True, text=True, timeout=120)
            tgz = work / f"brainrc-{VERSION}.tgz"
            if r.returncode or not tgz.is_file():
                raise RuntimeError(f"npm pack failed: {r.stderr[-400:]}")
            return f"npx --yes --package '{tgz}' brainrc status", extra
        if not public("https://github.com/brainrc/brainrc", work):
            raise Skip("github.com/brainrc/brainrc is not public")
        return "npx --yes github:brainrc/brainrc status", extra
    if route == "brew":
        brew = find_brew()
        if not brew:
            raise Skip("Homebrew not installed")
        bin_dir = str(Path(brew).parent)
        # Homebrew builds the sdist itself and fetches the build backend from PyPI: no offline pip.
        extra = {"HOMEBREW_NO_AUTO_UPDATE": "1", "HOMEBREW_NO_INSTALL_CLEANUP": "1",
                 "HOMEBREW_NO_ENV_HINTS": "1", "PATH_PREPEND": bin_dir}
        if local:
            sdist = local / f"brainrc-{VERSION}.tar.gz"
            if not sdist.is_file():
                raise RuntimeError(f"{sdist} missing: build it with python3 -m build")
            tap = local_tap(brew)
            (tap / "Formula").mkdir(parents=True, exist_ok=True)
            (tap / "Formula" / "brainrc.rb").write_text(local_formula(sdist))
            return f"brew install {LOCAL_TAP}/brainrc\nbrainrc status", extra
        if not public("https://github.com/brainrc/homebrew-tap", work):
            raise Skip("the brainrc/homebrew-tap tap doesn't exist yet")
        return "brew install brainrc/tap/brainrc\nbrainrc status", extra
    raise ValueError(route)


def local_formula(sdist: Path) -> str:
    """The release formula, with the sdist's URL replaced by the local file's."""
    https = render(version_of(sdist), f"https://local.invalid/{sdist.name}", sha256_of(sdist))
    return https.replace(f'url "https://local.invalid/{sdist.name}"', f'url "{sdist.resolve().as_uri()}"')


def local_tap(brew: str) -> Path:
    """A scratch tap for the local formula (Homebrew installs formulae only from taps)."""
    repo = subprocess.run([brew, "--repository"], capture_output=True, text=True, check=True).stdout.strip()
    user, name = LOCAL_TAP.split("/")
    tap = Path(repo, "Library", "Taps", user, f"homebrew-{name}")
    tap.mkdir(parents=True, exist_ok=True)
    return tap


def run_route(route: str, local: Path | None, limit: float) -> tuple[str, str]:
    """('PASS'|'FAIL'|'SKIP', detail)."""
    work = Path(tempfile.mkdtemp(prefix=f"install-time-{route}-"))
    try:
        try:
            script, extra = plan(route, local, work)
        except Skip as e:
            return "SKIP", str(e)
        home = work / "home"
        (home / ".claude").mkdir(parents=True)
        env = {k: v for k, v in os.environ.items() if k not in ENV_DROP}
        prepend = [str(home / ".local" / "bin")]
        if "PATH_PREPEND" in extra:
            prepend.append(extra.pop("PATH_PREPEND"))
        env.update(extra, HOME=str(home), USERPROFILE=str(home),
                   PATH=os.pathsep.join([*prepend, env.get("PATH", "")]))
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
            return "FAIL", f"{took:.1f} s to first status, over the {limit:.0f} s limit"
        return "PASS", f"{took:.1f} s to first status"
    finally:
        if route == "brew" and local:
            brew = find_brew()
            if brew:
                quiet([brew, "untap", "--force", LOCAL_TAP], timeout=120)
        shutil.rmtree(work, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--path", action="append", choices=PATHS, help="route to time (repeatable; default all)")
    ap.add_argument("--limit", type=float, default=60.0, help="seconds allowed to first status")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--local", type=Path, metavar="DIST_DIR", help="install this checkout's build")
    src.add_argument("--published", action="store_true", help="install the published releases (default)")
    args = ap.parse_args(argv)
    failed = False
    for route in args.path or PATHS:
        try:
            result, detail = run_route(route, args.local, args.limit)
        except Exception as e:  # a crash is a FAIL line, never a traceback
            result, detail = "FAIL", f"{type(e).__name__}: {e}"
        print(f"{result} {route}: {detail}", flush=True)
        failed = failed or result == "FAIL"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
