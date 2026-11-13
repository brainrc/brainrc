"""brainrc.lock: read it against its schema and write it in its one canonical form (docs/project.md)."""
from __future__ import annotations

import hashlib
import re
import tomllib
from pathlib import Path

from . import schema
from .config import ConfigError, tilde, toml_error

NAME = "brainrc.lock"
HEADER = "# brainrc.lock: written by brainrc. Don't edit it by hand."
VERSION = 1
BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")
PACK_KEYS = ("git", "ref", "commit", "path")
ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _string(text: str) -> str:
    """A TOML basic string."""
    out = []
    for c in text:
        if c in ESCAPES:
            out.append(ESCAPES[c])
        elif ord(c) < 0x20 or ord(c) == 0x7F:
            out.append(f"\\u{ord(c):04X}")
        else:
            out.append(c)
    return '"' + "".join(out) + '"'


def _key(key: str) -> str:
    return key if BARE_KEY.fullmatch(key) else _string(key)


def _value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return _string(value)


def _table(lines: list[str], header: str, entries: dict) -> None:
    lines += ["", f"[{header}]"] + [f"{_key(k)} = {_value(v)}" for k, v in sorted(entries.items())]


def dumps(data: dict) -> str:
    """The canonical text: a fixed key order, every table sorted, no timestamps."""
    lines = [HEADER] + [f"{k} = {_value(data[k])}" for k in ("version", "brainrc", "scope")]
    for key in sorted(data.get("packs", {})):
        pack = data["packs"][key]
        lines += ["", f"[packs.{_key(key)}]"] + [f"{k} = {_value(pack[k])}" for k in PACK_KEYS if k in pack]
        _table(lines, f"packs.{_key(key)}.files", pack.get("files", {}))
    for name in ("outputs", "blocks"):
        if data.get(name):
            _table(lines, name, data[name])
    return "\n".join(lines) + "\n"


def loads(text: str, where: str = NAME) -> dict:
    """Parse and check a lock's text; ConfigError names the file and every problem."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise toml_error(Path(where), text, e) from None
    if isinstance(data.get("version"), int) and not isinstance(data["version"], bool) and data["version"] > VERSION:
        raise ConfigError(f"{where}: lock version {data['version']} is newer than this brainrc reads "
                          f"({VERSION}); upgrade brainrc")
    problems = schema.errors(data, schema.load("brainrc.lock"))
    if problems:
        raise ConfigError(f"{where}: " + "; ".join(problems))
    return data


def read(path: Path) -> dict | None:
    """The lock at path, or None when there is none."""
    if not path.is_file():
        return None
    return loads(path.read_bytes().decode("utf-8"), tilde(path))


def write(path: Path, data: dict) -> bool:
    """Write the lock when its text changes; True if it did. Bytes, so `\\n` stays `\\n` everywhere."""
    text = dumps(data).encode("utf-8")
    if path.is_file() and path.read_bytes() == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(text)
    tmp.replace(path)
    return True
