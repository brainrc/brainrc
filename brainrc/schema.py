"""A small JSON Schema validator: the subset docs/schemas/ uses, so brainrc stays stdlib-only.

Supported keywords: type, const, enum, pattern, minLength, minimum, minItems, items, properties, required,
additionalProperties, propertyNames, $ref (to #/$defs/<name>), not, oneOf, anyOf. Anything else
in a schema is ignored, so a schema that needs more must grow this file first.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import config

TYPES = {"object": dict, "array": list, "string": str, "boolean": bool}


def _is(value, kind: str) -> bool:
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[kind])


def _where(path: tuple) -> str:
    """A path as `packs.gatework.ref`, quoting keys that aren't plain words."""
    out = ""
    for p in path:
        if isinstance(p, int):
            out += f"[{p}]"
        else:
            p = p if re.fullmatch(r"[A-Za-z0-9_-]+", p) else json.dumps(p)
            out += f".{p}" if out else p
    return out or "the file"


def errors(value, schema: dict, root: dict | None = None, path: tuple = (),
           unknown: list[tuple[tuple, str]] | None = None) -> list[str]:
    """Every way value fails schema, as `<where>: <what>`; [] when it conforms. With unknown, a key
    that additionalProperties: false refuses goes there instead, as (path of its table, key), so a
    caller can warn about it (a typo) rather than fail."""
    root = root if root is not None else schema
    if "$ref" in schema:
        name = schema["$ref"].removeprefix("#/$defs/")
        return errors(value, root["$defs"][name], root, path, unknown)
    where = _where(path)
    kind = schema.get("type")
    if kind and not _is(value, kind):
        return [f"{where}: must be {'an' if kind[0] in 'aeiou' else 'a'} {kind}"]
    found = []
    if "const" in schema and value != schema["const"]:
        found.append(f"{where}: must be {json.dumps(schema['const'])}")
    if "enum" in schema and value not in schema["enum"]:
        found.append(f"{where}: must be one of {', '.join(json.dumps(e) for e in schema['enum'])}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            found.append(f"{where}: must not be empty")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            found.append(f"{where}: {json.dumps(value)} is not allowed here")
    if "minimum" in schema and isinstance(value, (int, float)) and not isinstance(value, bool) \
            and value < schema["minimum"]:
        found.append(f"{where}: must be at least {schema['minimum']}")
    if isinstance(value, list) and len(value) < schema.get("minItems", 0):
        found.append(f"{where}: must not be empty")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            found += errors(item, schema["items"], root, path + (i,), unknown)
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                found.append(f"{where}: `{key}` is required")
        for key, item in value.items():
            if "propertyNames" in schema and errors(key, schema["propertyNames"], root):
                found.append(f"{where}: key {json.dumps(key)} is not allowed")
            if key in props:
                found += errors(item, props[key], root, path + (key,), unknown)
            elif schema.get("additionalProperties") is False:
                if unknown is None:
                    found.append(f"{where}: unknown key `{key}`")
                else:
                    unknown.append((path, key))
            elif isinstance(schema.get("additionalProperties"), dict):
                found += errors(item, schema["additionalProperties"], root, path + (key,), unknown)
    if "not" in schema and not errors(value, schema["not"], root, path):
        found.append(f"{where}: {_not_message(schema['not'])}")
    if "anyOf" in schema:
        matched = _matches(value, schema["anyOf"], root, path, unknown)
        if not matched:
            found.append(f"{where}: matches none of the allowed forms")
        elif unknown is not None:
            unknown += matched[0]
    if "oneOf" in schema:
        matched = _matches(value, schema["oneOf"], root, path, unknown)
        if len(matched) != 1:
            found.append(f"{where}: {_one_of_message(value, schema['oneOf'])}")
        elif unknown is not None:
            unknown += matched[0]
    return found


def _matches(value, forms: list[dict], root: dict, path: tuple, unknown: list | None) -> list[list]:
    """The unknown keys of each form value matches. When unknown keys are collected, a form whose
    only problem is an unknown key still matches (the key is a warning, not a failure)."""
    found = []
    for form in forms:
        mine = [] if unknown is not None else None
        if not errors(value, form, root, path, mine):
            found.append(mine or [])
    return found


def _not_message(schema: dict) -> str:
    keys = schema.get("required")
    if keys:
        return f"set only one of {', '.join(f'`{k}`' for k in keys)}"
    return "has a form that isn't allowed"


def _one_of_message(value, forms: list[dict]) -> str:
    """For a pack: name the keys each allowed form needs."""
    shapes = [" + ".join(f"`{k}`" for k in s.get("required", [])) for s in forms]
    return f"needs exactly one of: {'; '.join(shapes)}" if all(shapes) else "matches more or less than one allowed form"


_SCHEMAS: dict[str, dict] = {}


def load(name: str) -> dict:
    """docs/schemas/<name>.schema.json from core (bundled with an installed package)."""
    if name not in _SCHEMAS:
        _SCHEMAS[name] = json.loads((schema_dir() / f"{name}.schema.json").read_text(encoding="utf-8"))
    return _SCHEMAS[name]


def schema_dir() -> Path:
    return config.REPO / "docs" / "schemas"
