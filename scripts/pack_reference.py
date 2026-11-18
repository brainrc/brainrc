#!/usr/bin/env python3
"""Write the key tables in docs/packs.md from the JSON Schemas in docs/schemas/.

Each table sits between a `<!-- generated: <schema> -->` line and `<!-- end generated -->`.
With no options, exit 1 when a table differs from what the schema gives; --write rewrites them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "packs.md"
SCHEMAS = REPO / "docs" / "schemas"
# schema file -> where its keys are: the top level, or one entry of a table of them
TABLES = {
    "pack.toml.schema.json": ("properties",),
    "mcp-servers.toml.schema.json": ("$defs", "server", "properties"),
}
BLOCK = re.compile(r"(<!-- generated: (?P<schema>[\w.-]+) -->\n)(?P<body>.*?)(<!-- end generated -->)", re.S)
DOC_LINK = re.compile(r"\(docs/(?P<page>[\w/-]+\.md)#(?P<anchor>[\w-]+)\)")


def link(m: re.Match[str]) -> str:
    """`(docs/packs.md#naming)` -> `([naming](#naming))`, relative to docs/packs.md."""
    page, anchor = m["page"], m["anchor"]
    target = f"#{anchor}" if page == DOC.name else f"{page}#{anchor}"
    return f"([{anchor.replace('-', ' ')}]({target}))"


def kind(spec: dict) -> str:
    t = spec.get("type", "any")
    if t == "array":
        return f"array of {spec.get('items', {}).get('type', 'any')}s"
    if t == "object":
        return "table"
    return t


def table(schema: dict, path: tuple[str, ...]) -> str:
    props = schema
    for key in path:
        props = props[key]
    rows = ["| Key | Type | What it is |", "|---|---|---|"]
    for key, spec in props.items():
        # escape what Markdown would read as HTML or a column break
        text = spec.get("description", "").replace("<", "&lt;").replace("|", "\\|")
        text = DOC_LINK.sub(link, text)
        rows.append(f"| `{key}` | {kind(spec)} | {text} |")
    return "\n".join(rows) + "\n"


def render(doc: str) -> str:
    seen: set[str] = set()

    def fill(m: re.Match[str]) -> str:
        name = m["schema"]
        if name not in TABLES:
            raise SystemExit(f"{DOC.name}: no schema table named {name}")
        seen.add(name)
        schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
        return m.group(1) + table(schema, TABLES[name]) + m.group(4)

    out = BLOCK.sub(fill, doc)
    missing = sorted(set(TABLES) - seen)
    if missing:
        raise SystemExit(f"{DOC.name}: no generated block for {', '.join(missing)}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="rewrite the tables instead of checking them")
    args = ap.parse_args(argv)
    doc = DOC.read_text(encoding="utf-8")
    new = render(doc)
    if new == doc:
        print(f"{DOC.relative_to(REPO)}: key tables match the schemas")
        return 0
    if args.write:
        DOC.write_text(new, encoding="utf-8")
        print(f"{DOC.relative_to(REPO)}: key tables rewritten")
        return 0
    print(f"{DOC.relative_to(REPO)}: key tables differ from the schemas; run scripts/pack_reference.py --write")
    return 1


if __name__ == "__main__":
    sys.exit(main())
