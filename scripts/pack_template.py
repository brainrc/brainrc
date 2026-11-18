#!/usr/bin/env python3
"""Keep examples/pack-template, the contents of the brainrc/pack-template repository, in step
with what `brainrc new pack` writes.

The template is `new pack mypack` (with CLAUDE.md and GEMINI.md) and a README section on making
it yours. With no options, exit 1 when it differs; the brainrc version it pins is read from the
template itself, so a patch release doesn't make it stale. --write rewrites it at this VERSION.
"""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from brainrc.newpack import Answers, spec_for  # noqa: E402
from brainrc.scaffold import render_pack  # noqa: E402

sources = importlib.import_module("brainrc.sources")  # the package also has a sources() function

TEMPLATE = REPO / "examples" / "pack-template"
NAME = "mypack"
PIN = re.compile(r"^\s*rev: v(\d+)\.(\d+)\.(\d+)\s*$", re.M)
INTRO = """\
# mypack

A template for a [brainrc](https://github.com/brainrc/brainrc) pack. Use it from GitHub
(**Use this template**), then make it yours before you add anything:

1. Pick a name and a prefix that follow brainrc's
   [naming rules](https://github.com/brainrc/brainrc/blob/main/docs/packs.md#naming), for example
   `acme` and `acme-`.
2. In `pack.toml`, set `name`, `prefix` and `description`.
3. Rename `rules/10-mypack.md` and `skills/mypack-facts/`, and change `mypack` in that skill's
   `name:` and in the rule.
4. Replace this section, and `mypack` below, with your pack's name.
5. Run `grep -rn mypack .` to find what's left, then `brainrc validate --pack .`.

Or skip the template: `brainrc new pack acme` writes the same files with your name in them.

"""


def files(version: tuple[int, ...]) -> dict[str, str]:
    """The template's files at a brainrc version: what `new pack` writes, with INTRO on top."""
    with mock.patch.object(sources, "core_version", return_value=version):
        out = render_pack(spec_for(Answers(NAME, harnesses=["claude", "gemini"])))
    readme = out["README.md"]
    assert readme.startswith(f"# {NAME}\n\n"), "README.md starts with the pack's name"
    out["README.md"] = INTRO + readme[len(f"# {NAME}\n\n"):]
    return out


def pinned(template: Path = TEMPLATE) -> tuple[int, ...] | None:
    path = template / ".pre-commit-config.yaml"
    m = PIN.search(path.read_text(encoding="utf-8")) if path.is_file() else None
    return tuple(map(int, m.groups())) if m else None


def on_disk(template: Path = TEMPLATE) -> dict[str, str]:
    return {p.relative_to(template).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(template.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def differences(template: Path = TEMPLATE) -> list[str]:
    """What differs between the template and `new pack` at the version the template pins."""
    version = pinned(template)
    if version is None:
        return [f"{template.name}/.pre-commit-config.yaml: no `rev: vX.Y.Z` line"]
    want, have = files(version), on_disk(template)
    out = [f"missing {rel}" for rel in want if rel not in have]
    out += [f"extra {rel}" for rel in have if rel not in want]
    out += [f"differs {rel}" for rel in want if rel in have and have[rel] != want[rel]]
    return out


def write(template: Path = TEMPLATE) -> None:
    want = files(sources.core_version())
    for rel in on_disk(template):
        if rel not in want:
            (template / rel).unlink()
    for rel, text in want.items():
        path = template / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="rewrite the template at this VERSION")
    args = ap.parse_args(argv)
    if args.write:
        write()
        print(f"{TEMPLATE.relative_to(REPO)}: rewritten")
        return 0
    diff = differences()
    for line in diff:
        print(f"{TEMPLATE.relative_to(REPO)}: {line}")
    if diff:
        print("run scripts/pack_template.py --write")
        return 1
    print(f"{TEMPLATE.relative_to(REPO)}: matches `brainrc new pack`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
