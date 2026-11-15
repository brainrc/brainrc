#!/usr/bin/env python3
"""Write the Homebrew formula for a release: Formula/brainrc.rb in the brainrc/homebrew-tap repo.

Usage: python3 scripts/homebrew_formula.py SDIST [--url URL | --pypi-json PATH] [--out PATH]
SDIST is the release's brainrc-<X.Y.Z>.tar.gz; its name gives the version and its bytes the
sha256. The formula fetches it from PyPI: by default from PyPI's stable source URL; with
--pypi-json (PyPI's JSON for that version, https://pypi.org/pypi/brainrc/<X.Y.Z>/json, which the
release workflow downloads) from the file URL listed there, after checking that PyPI's sha256
matches SDIST. --url names any other URL. Prints the formula, or writes it to --out. Makes no
network calls. brainrc needs nothing outside the standard library, so the formula has no resources.
Exits 1 on a bad input or a PyPI listing without the sdist yet, which a later try may fix, and 3
when PyPI's sdist has another sha256 than SDIST, which no retry fixes.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

NAME = re.compile(r"^brainrc-(\d+\.\d+\.\d+)\.tar\.gz$")
SOURCE_URL = "https://files.pythonhosted.org/packages/source/b/brainrc/brainrc-{version}.tar.gz"
PYTHON = "python@3.13"

FORMULA = '''# Written by brainrc's release workflow (scripts/homebrew_formula.py in brainrc/brainrc).
# Edits here are overwritten on the next release.
class Brainrc < Formula
  include Language::Python::Virtualenv

  desc "Sync skills, agents, rules and guard hooks into AI coding tools"
  homepage "https://github.com/brainrc/brainrc"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "{python}"

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      Each version installs to its own directory, and links into the old one break when Homebrew
      cleans it up. After `brew upgrade brainrc`, run `brainrc apply --repair`.
    EOS
  end

  test do
    assert_equal "brainrc #{{version}}", shell_output("#{{bin}}/brainrc --version").strip
  end
end
'''


class FormulaError(Exception):
    pass


class ShaMismatch(FormulaError):
    """PyPI holds another file under this version: retrying won't change it."""


def version_of(sdist: Path) -> str:
    m = NAME.match(sdist.name)
    if not m:
        raise FormulaError(f"{sdist.name}: expected brainrc-<X.Y.Z>.tar.gz")
    return m.group(1)


def sha256_of(sdist: Path) -> str:
    return hashlib.sha256(sdist.read_bytes()).hexdigest()


def render(version: str, url: str, sha256: str) -> str:
    if not url.startswith("https://") or '"' in url or "#" in url:
        raise FormulaError(f"refusing URL {url!r}: needs https and no quotes or #")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise FormulaError(f"not a sha256: {sha256!r}")
    if not url.endswith(f"/brainrc-{version}.tar.gz"):
        raise FormulaError(f"{url} is not brainrc-{version}.tar.gz")
    return FORMULA.format(url=url, sha256=sha256, python=PYTHON)


def pypi_url(listing: dict, version: str, sha256: str) -> str:
    """The sdist's file URL from PyPI's JSON for `version`; FormulaError unless its sha256 matches."""
    try:
        listed = (listing.get("info") or {}).get("version", version)
        sdists = [u for u in listing.get("urls") or [] if u.get("packagetype") == "sdist"]
        found = (sdists[0].get("digests") or {}).get("sha256") if sdists else None
        url = sdists[0].get("url") if sdists else None
    except AttributeError as e:
        raise FormulaError(f"unexpected PyPI JSON: {e}") from None
    if listed != version:
        raise FormulaError(f"the PyPI JSON is for {listed}, not {version}")
    if not sdists:
        raise FormulaError(f"PyPI lists no sdist for brainrc {version}")
    if found != sha256:
        raise ShaMismatch(f"PyPI's sdist for {version} has sha256 {found}, the release built {sha256}")
    if not isinstance(url, str):
        raise FormulaError(f"PyPI's sdist for {version} has no URL")
    return url


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sdist", type=Path)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--url", help="where the formula downloads the sdist")
    src.add_argument("--pypi-json", type=Path, help="PyPI's JSON for the version: use its sdist URL, "
                     "after checking its sha256")
    ap.add_argument("--out", type=Path, help="write the formula here instead of printing it")
    args = ap.parse_args(argv)
    try:
        version, sha256 = version_of(args.sdist), sha256_of(args.sdist)
        if args.pypi_json:
            url = pypi_url(json.loads(args.pypi_json.read_text()), version, sha256)
        else:
            url = args.url or SOURCE_URL.format(version=version)
        formula = render(version, url, sha256)
    except (FormulaError, OSError, ValueError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 3 if isinstance(e, ShaMismatch) else 1
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(formula)
    else:
        print(formula, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
