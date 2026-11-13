"""brainrc.lock: read it against its schema and write it in its one canonical form (docs/project.md)."""
from __future__ import annotations

import hashlib
import re
import tomllib
from pathlib import Path

from . import config, schema
from .config import KINDS, ConfigError, _layered, tilde, toml_error
from .packs import head
from .sources import Source, core_version, installed_items, markdown_files, tree_files

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


def clean_url(url: str) -> str:
    """A git URL as the lock records it: no user name or password for http(s), no password for
    other schemes, so a token in packs.local.toml never reaches a committed file."""
    m = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*://)([^/@]*)@(.*)$", url)
    if not m:
        return url
    scheme, user, rest = m.groups()
    if scheme.lower() in ("http://", "https://"):
        return scheme + rest
    return scheme + (user.split(":", 1)[0] + "@" if user else "") + rest


def shown_path(path: str) -> str:
    """A path pack's directory as its config wrote it, with an absolute path under ~ written with ~."""
    p = Path(path)
    return tilde(p) if p.is_absolute() else path


def pack_files(src: Source, items: list[Path], hooks: bool) -> dict[str, str]:
    """The pack's installed files (docs/project.md), by path in the pack, to their hashes: pack.toml,
    its validator, its rules, every file of each installed item and, with hooks, overrides/."""
    found: list[tuple[str, Path]] = []
    root = src.root

    def add(path: Path) -> None:
        if path.is_file():
            found.append((path.relative_to(root).as_posix(), path))

    add(root / "pack.toml")
    if isinstance(src.meta.get("validator"), str):
        add(root / src.meta["validator"])
    for rule in markdown_files("rules", src):
        add(rule)
    for item in items:
        if item.is_dir():
            found += [(f"{item.relative_to(root).as_posix()}/{rel}", f) for rel, f in tree_files(item)]
        else:
            add(item)
    if hooks and (root / "overrides").is_dir():
        found += [(f"overrides/{rel}", f) for rel, f in tree_files(root / "overrides")]
    return {rel: digest(f.read_bytes()) for rel, f in sorted(found)}


def pack_entry(cfg: dict, root: Path, files: dict[str, str]) -> dict:
    """One `[packs.<key>]` table: git, ref and the commit checked out, or the path."""
    if "git" in cfg:
        commit = head(root)
        if commit is None:
            raise ConfigError(f"{tilde(root)}: can't read the commit checked out (git rev-parse HEAD)")
        return {"git": clean_url(str(cfg["git"])), "ref": str(cfg.get("ref", "HEAD")), "commit": commit,
                "files": files}
    return {"path": shown_path(str(cfg["path"])), "files": files}


def new_lock(scope: str, packs: dict[str, dict], **tables: dict) -> dict:
    data = {"version": VERSION, "brainrc": ".".join(map(str, core_version())), "scope": scope, "packs": packs}
    data.update({k: v for k, v in tables.items() if v})
    return data


def moved(old: dict | None, key: str, entry: dict) -> str | None:
    """A note when the lock had this pack at the same URL and ref but another commit: a moved tag
    or branch. None otherwise."""
    was = (old or {}).get("packs", {}).get(key, {})
    if "commit" not in entry or was.get("git") != entry["git"] or was.get("ref") != entry["ref"] \
            or was.get("commit") in (None, entry["commit"]):
        return None
    return f"{entry['ref']}: {was['commit'][:12]} -> {entry['commit'][:12]}"


def user_lock_path() -> Path:
    return config.settings_home() / NAME


def user_lock(srcs: list[Source]) -> dict:
    """The user scope's lock: every enabled pack this machine installed, and what it installed."""
    layered = _layered("packs")
    packs = {}
    for src in srcs:
        if not src.is_core:
            items = [p for kind in KINDS for p in installed_items(src, kind)]
            packs[src.key] = pack_entry(layered[src.key], src.root, pack_files(src, items, config.installs("hooks")))
    return new_lock("user", packs)


def report_moved(old: dict | None, new: dict, label: str) -> None:
    """A MOVED line for each git pack whose ref now resolves to another commit than the lock had."""
    for key, entry in sorted(new.get("packs", {}).items()):
        note = moved(old, key, entry)
        if note:
            print(f"{'MOVED':9} {key:9} {note}  ({label})")
