"""The pack API: the version of what packs can rely on, apart from core's own version (#174).

Packs pin it with `requires_api = "^1"`, so a core release that changes only content (skills,
rules, docs, fixes) never breaks a pin. `contract()` lists what that version freezes, read from
the schemas and the code that enforce it. docs/schemas/pack-api/<version>.json holds the frozen
copy of each released version, and its digest is in FROZEN, so a contract change fails the tests
until PACK_API moves: MINOR when every old entry is still there, MAJOR otherwise.

    python3 scripts/pack_api.py            # print the live contract
    python3 scripts/pack_api.py --write    # freeze it as docs/schemas/pack-api/<PACK_API>.json
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from . import config

PACK_API = "1.0"

# Digest of each frozen docs/schemas/pack-api/<version>.json. A released version never changes:
# change the contract, then add a version here (and its file) instead of editing one.
FROZEN = {
    "1.0": "c83b5273bac4ed44e484c7a102716ee11dab866e9ea404729fcd8b3e2a52a6b9",
}

SCHEMAS = {"pack.toml": "pack.toml.schema.json", "mcp/servers.toml": "mcp-servers.toml.schema.json"}

# Where a pack's files go and what each needs, as docs/packs.md#layout and docs/formats.md list
# them. The schemas above cover what is inside pack.toml and mcp/servers.toml.
LAYOUT = (
    "pack.toml",
    "skills/<prefix>*/SKILL.md: frontmatter name (= folder), description",
    "agents/<prefix>*.md: frontmatter name (= file stem), description; optional model, tools",
    "commands/<prefix>*.md: frontmatter description",
    "rules/NN-*.md: frontmatter trigger, alwaysApply: true; rendered after core's rules",
    "overrides/claude/hooks/: linked to <hooks_dir>-<name>",
    "overrides/claude/settings.fragment.json: merged after core's; {{hooks_dir}} placeholder",
    "overrides/opencode/plugin.js: linked as brainrc-guard-<name>.js",
    "mcp/servers.toml",
    "tripwires.toml: [[tripwire]] pattern, message, allow, paths, exclude",
    "validator: a Python module in the pack (pack.toml `validator`)",
    "tests: unittest tests that validate --pack runs (pack.toml `test`)",
    "extensions.md: rendered from [extensions.*] and validator render_extensions",
    "naming: skills, agents, commands and MCP servers start with the pack's prefix",
)

PLUGIN_NAME = re.compile(r'(?:hasattr|getattr)\([\w\[\]]+, "([A-Za-z_]+)"')
PLUGIN_CALL = '_call(me, mod, "'
# Schema keywords read as structure (walked) or prose (left out); every other keyword's value is
# an entry as written, so a change to oneOf, not, maxLength or additionalProperties shows too.
WALKED = {"$ref", "properties", "additionalProperties", "propertyNames", "items", "required", "$defs"}
PROSE = {"description", "title", "$schema", "$id", "$comment", "examples", "default"}


def _plain(value):
    """value without descriptions or titles, for an entry that holds a whole subtree."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items() if k not in PROSE}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _schema_entries(label: str, node: dict, root: dict, where: str = "") -> set[str]:
    """One entry per key path and each keyword the schema gives it there (descriptions left out)."""
    if "$ref" in node:
        node = {**root["$defs"][node["$ref"].split("/")[-1]], **{k: v for k, v in node.items() if k != "$ref"}}
    head = f"{label} {where or '.'}"
    out = {f"{head}: {key} {json.dumps(_plain(value), sort_keys=True)}"
           for key, value in node.items() if key not in WALKED | PROSE}
    for name in node.get("required", ()):
        out.add(f"{head}: requires {name}")
    for name, sub in node.get("properties", {}).items():
        out |= _schema_entries(label, sub, root, f"{where}.{name}" if where else name)
    extra = node.get("additionalProperties")
    if isinstance(extra, dict):
        out |= _schema_entries(label, extra, root, f"{where}.*")
    elif extra is not None:
        out.add(f"{head}: additionalProperties {json.dumps(extra)}")
    if "propertyNames" in node:
        out |= _schema_entries(label, node["propertyNames"], root, f"{where}.<key>")
    if "items" in node:
        out |= _schema_entries(label, node["items"], root, f"{where}[]")
    return out


def _validator_entries(text: str) -> set[str]:
    """Each module-level name core reads from a pack's validator, and each function core calls
    with the number of arguments it passes (a new argument breaks every validator that has it)."""
    out = {f"validator {name}" for name in PLUGIN_NAME.findall(text)}
    at = text.find(PLUGIN_CALL)
    while at != -1:
        name_end = text.index('"', at + len(PLUGIN_CALL))
        name, depth, args, i = text[at + len(PLUGIN_CALL):name_end], 1, 0, name_end + 1
        while depth:  # count the top-level commas after the name, up to the call's closing paren
            c = text[i]
            depth += (c in "([{") - (c in ")]}")
            args += c == "," and depth == 1
            i += 1
        out.add(f"validator {name}({args} arguments)")
        at = text.find(PLUGIN_CALL, i)
    return out


def contract() -> list[str]:
    """What pack API PACK_API promises packs, one sorted line per thing a pack can rely on."""
    from . import naming  # naming imports sources, which imports this module
    out = set()
    for label, file in SCHEMAS.items():
        schema = json.loads((config.REPO / "docs" / "schemas" / file).read_text(encoding="utf-8"))
        out |= _schema_entries(label, schema, schema)
    out |= {f"layout {line}" for line in LAYOUT}
    out |= {f"kind {kind}" for kind in config.KINDS}
    out |= {f"agent model {model}" for model in config.KNOWN_MODELS}
    out |= {f"naming name {naming.NAME.pattern}", f"naming id {naming.PACK_ID.pattern}",
            f"naming item {config.SKILL_NAME.pattern}"}
    plugins = (Path(__file__).parent / "plugins.py").read_text(encoding="utf-8")
    out |= _validator_entries(plugins)
    return sorted(out)


def frozen_path(version: str) -> Path:
    return config.REPO / "docs" / "schemas" / "pack-api" / f"{version}.json"


def render(version: str, entries: list[str]) -> str:
    return json.dumps({"pack_api": version, "contract": entries}, indent=2) + "\n"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def version_tuple(version: str) -> tuple[int, int, int]:
    """'1.0' -> (1, 0, 0), padded as parse_constraint pads its bounds."""
    parts = [int(n) for n in version.split(".")]
    return tuple(parts + [0] * (3 - len(parts)))


def _frozen(version: str) -> list[str]:
    return json.loads(frozen_path(version).read_text(encoding="utf-8"))["contract"]


def check() -> list[str]:
    """Problems with the frozen contracts: [] while the live contract is PACK_API's, every frozen
    file is unchanged, and each MINOR bump keeps every entry of the version before it."""
    fix = (f"bump PACK_API (MINOR if nothing was removed, MAJOR otherwise), run "
           f"`python3 scripts/pack_api.py --write` and add the digest it prints to FROZEN")
    files = {p.stem for p in frozen_path(PACK_API).parent.glob("*.json")}
    problems = []
    for version in sorted(set(FROZEN) | files, key=version_tuple):
        rel = f"docs/schemas/pack-api/{version}.json"
        if version not in files:
            problems.append(f"FROZEN lists pack API {version}, but {rel} is missing")
        elif version not in FROZEN:
            problems.append(f"{rel} has no digest in FROZEN")
        elif digest(frozen_path(version).read_text(encoding="utf-8")) != FROZEN[version]:
            problems.append(f"{rel} changed, but a released pack API never changes: restore it, then {fix}")
    if problems:
        return problems
    versions = sorted(FROZEN, key=version_tuple)
    if PACK_API != versions[-1]:
        return [f"PACK_API is {PACK_API}, but FROZEN goes up to {versions[-1]}"]
    for old, new in zip(versions, versions[1:]):
        gone = sorted(set(_frozen(old)) - set(_frozen(new)))
        if version_tuple(old)[0] == version_tuple(new)[0] and gone:
            problems.append(f"pack API {new} drops what {old} promised, so it needs a MAJOR bump: {gone}")
    live, frozen = set(contract()), set(_frozen(PACK_API))
    if live != frozen:
        problems.append(f"the pack contract changed but PACK_API is still {PACK_API} "
                        f"(added {sorted(live - frozen)}, removed {sorted(frozen - live)}): {fix}")
    return problems


def main(argv: list[str]) -> int:
    text = render(PACK_API, contract())
    if argv == ["--write"]:
        path = frozen_path(PACK_API)
        if PACK_API in FROZEN or path.exists():  # rewriting a released version would hide the change
            print(f"pack API {PACK_API} is already frozen; bump PACK_API first (MINOR if nothing was "
                  "removed, MAJOR otherwise), then run --write again")
            return 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(config.REPO).as_posix()}; set FROZEN[{PACK_API!r}] = {digest(text)!r}")
        return 0
    sys.stdout.write(text)
    return 0
