"""A small JSON Schema validator: the subset docs/schemas/ uses, so brainrc stays stdlib-only.

Supported keywords: type, const, enum, pattern, minLength, items, properties, required,
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


def errors(value, schema: dict, root: dict | None = None, path: tuple = ()) -> list[str]:
    """Every way value fails schema, as `<where>: <what>`; [] when it conforms."""
    root = root if root is not None else schema
    if "$ref" in schema:
        name = schema["$ref"].removeprefix("#/$defs/")
        return errors(value, root["$defs"][name], root, path)
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
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            found += errors(item, schema["items"], root, path + (i,))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                found.append(f"{where}: `{key}` is required")
        for key, item in value.items():
            if "propertyNames" in schema and errors(key, schema["propertyNames"], root):
                found.append(f"{where}: key {json.dumps(key)} is not allowed")
            if key in props:
                found += errors(item, props[key], root, path + (key,))
            elif schema.get("additionalProperties") is False:
                found.append(f"{where}: unknown key `{key}`")
            elif isinstance(schema.get("additionalProperties"), dict):
                found += errors(item, schema["additionalProperties"], root, path + (key,))
    if "not" in schema and not errors(value, schema["not"], root, path):
        found.append(f"{where}: {_not_message(schema['not'])}")
    if "anyOf" in schema and all(errors(value, s, root, path) for s in schema["anyOf"]):
        found.append(f"{where}: matches none of the allowed forms")
    if "oneOf" in schema:
        matched = [s for s in schema["oneOf"] if not errors(value, s, root, path)]
        if len(matched) != 1:
            found.append(f"{where}: {_one_of_message(value, schema['oneOf'])}")
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
        _SCHEMAS[name] = json.loads((schema_dir() / f"{name}.schema.json").read_text())
    return _SCHEMAS[name]


def schema_dir() -> Path:
    return config.REPO / "docs" / "schemas"
