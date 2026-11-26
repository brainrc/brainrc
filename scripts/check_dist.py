#!/usr/bin/env python3
"""Check the sdist and wheel that `python3 -m build` wrote, before they go to PyPI.

Usage: python3 scripts/check_dist.py DIST_DIR
DIST_DIR must hold exactly brainrc-<VERSION>.tar.gz and brainrc-<VERSION>-py3-none-any.whl. The
sdist carries only what the wheel is built from (no specs/, tests/ or evals/), the wheel bundles
core under brainrc/_core/ and declares no dependencies (brainrc is stdlib-only). Prints one
PASS/FAIL line per check and each file's sha256; exits 1 on any FAIL.
"""
import hashlib
import sys
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def force_include(repo: Path = REPO) -> dict[str, str]:
    """pyproject.toml's wheel force-include: source path in the sdist -> path in the wheel."""
    pyproject = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]


def templates(repo: Path = REPO) -> list[str]:
    """The files under brainrc/_templates that `brainrc new pack` and `new <item>` read, as wheel paths."""
    root = repo / "brainrc" / "_templates"
    return sorted(p.relative_to(repo).as_posix() for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def has(names: list[str], path: str) -> bool:
    """The archive holds `path`, as a file or as a directory with something in it."""
    return any(n == path or n.startswith(path + "/") for n in names)


NOT_IN_SDIST = ("specs", "tests", "evals", "examples", "scripts", ".github", "changelog.d")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(dist: Path, version: str, core: dict[str, str] | None = None) -> list[tuple[str, bool, str]]:
    core = force_include() if core is None else core
    if not dist.is_dir():
        return [("files", False, f"{dist} is not a directory")]
    results = []
    sdist, wheel = dist / f"brainrc-{version}.tar.gz", dist / f"brainrc-{version}-py3-none-any.whl"
    names = sorted(p.name for p in dist.iterdir() if p.is_file())
    results.append(("files", names == sorted([sdist.name, wheel.name]),
                    f"expected {sdist.name} and {wheel.name}, found {names}"))
    if sdist.is_file():
        with tarfile.open(sdist) as tf:
            members = [m.name.split("/", 1)[1] for m in tf.getmembers() if "/" in m.name]
        top = {m.split("/", 1)[0] for m in members}
        extra = sorted(top & set(NOT_IN_SDIST))
        results.append(("sdist leaves out specs, tests and tooling", not extra, f"has {extra}"))
        missing = [src for src in core if not has(members, src)]
        results.append(("sdist carries core", not missing, f"missing {missing}"))
    if wheel.is_file():
        with zipfile.ZipFile(wheel) as zf:
            files = zf.namelist()
            info = f"brainrc-{version}.dist-info/METADATA"
            meta = Parser().parsestr(zf.read(info).decode() if info in files else "")
        results.append(("wheel version", meta["Version"] == version, f"METADATA says {meta['Version']}"))
        results.append(("wheel needs Python 3.11+", meta["Requires-Python"] == ">=3.11",
                        f"Requires-Python {meta['Requires-Python']}"))
        deps = meta.get_all("Requires-Dist") or []
        results.append(("wheel has no dependencies", not deps, f"Requires-Dist {deps}"))
        missing = [dest for dest in core.values() if not has(files, dest)]
        results.append(("wheel bundles core", not missing, f"missing {missing}"))
        missing = [rel for rel in templates() if rel not in files]
        results.append(("wheel carries the `new pack` templates", not missing, f"missing {missing}"))
    return results


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(__doc__.strip().splitlines()[2])
        return 2
    dist = Path(args[0])
    version = (REPO / "VERSION").read_text().strip()
    failed = False
    for name, ok, detail in check(dist, version):
        print(f"{'PASS' if ok else 'FAIL'} {name}" + ("" if ok else f": {detail}"))
        failed = failed or not ok
    if not failed:
        for p in sorted(dist.iterdir()):
            print(f"sha256 {sha256(p)}  {p.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
