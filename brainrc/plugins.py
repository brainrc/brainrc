"""Validator plugins (#172): checks and renders a pack ships as its own Python.

pack.toml `validator = "<file>.py"` names a module in the pack's root. It is the pack's code running
inside brainrc, so core loads it only for a bundled pack, for the pack `validate --pack` checks,
and for a pack whose packs.toml entry sets `run_validator = true`. Every name is optional:

  NAMESPACE          its table under any pack's [extensions] (default: the pack's name)
  LEGACY_KEYS        top-level [extensions] keys it still reads, with a warning until REMOVED_IN
  LEGACY_NAMESPACES  older table names it still reads, the same way
  check_extensions(table, where, skill_names, agent_names) -> errors in one pack's table
  check(me, srcs)    -> errors across every source (validate); `me` is the plugin's own pack
  doctor(me)         -> [(FAIL | WARN, what is wrong, how to fix it)]
  render_extensions(tables) -> the text apply writes to $BRAINRC_HOME/extensions.md, from
                        [(pack name, its table)] for every other enabled pack
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from types import ModuleType

from .config import ConfigError, _layered
from .sources import Source

_LOADED: dict[tuple[str, int], ModuleType] = {}


def trusted(src: Source) -> bool:
    """A bundled pack, the pack `validate --pack` checks (no packs.toml key), or one the user opted in."""
    if src.bundled or not src.key:
        return True
    return bool(_layered("packs").get(src.key, {}).get("run_validator"))


def load(src: Source) -> ModuleType | None:
    """src's validator module, or None when it has none or isn't trusted."""
    name = src.meta.get("validator")
    if name is None or src.is_core or not trusted(src):
        return None
    path = (src.root / str(name)).resolve()
    if path.suffix != ".py" or not path.is_relative_to(src.root.resolve()) or not path.is_file():
        raise ConfigError(f"{src.name}:pack.toml: `validator` must name a .py file in the pack ({name})")
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _LOADED:
        module_name = "brainrc_validator_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        dont_write, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # never write into a pack
        try:
            spec.loader.exec_module(module)
        except Exception as e:  # noqa: BLE001  (any error in a pack's code is the pack's)
            raise ConfigError(f"{src.name}:{name}: validator failed to load ({type(e).__name__}: {e})") from None
        finally:
            sys.dont_write_bytecode = dont_write
        _LOADED[key] = module
    return _LOADED[key]


def validators(srcs: list[Source]) -> list[tuple[Source, ModuleType]]:
    return [(src, mod) for src in srcs if (mod := load(src))]


def namespace(me: Source, mod: ModuleType) -> str:
    return getattr(mod, "NAMESPACE", me.name)


def table(src: Source, me: Source, mod: ModuleType) -> dict:
    """src's [extensions] for this plugin: legacy top-level keys, then older tables, then its own."""
    ext = src.meta.get("extensions", {})
    found = {k: v for k, v in ext.items() if k in getattr(mod, "LEGACY_KEYS", ())}
    for ns in (*getattr(mod, "LEGACY_NAMESPACES", ()), namespace(me, mod)):
        if isinstance(ext.get(ns), dict):
            found.update(ext[ns])
    return found


def extension_errors(src: Source, plugins: list[tuple[Source, ModuleType]],
                     skill_names: set[str], agent_names: set[str]) -> list[str]:
    errors = []
    for me, mod in plugins:
        if hasattr(mod, "check_extensions") and (t := table(src, me, mod)):
            errors += mod.check_extensions(t, f"{src.name}:pack.toml", skill_names, agent_names)
    return errors


def extension_warnings(srcs: list[Source], plugins: list[tuple[Source, ModuleType]]) -> list[str]:
    """Old extension forms, tables no enabled pack reads, and validators core won't run."""
    owners = {namespace(me, mod): (me, mod) for me, mod in plugins}
    legacy = {k: (me, mod) for me, mod in plugins for k in getattr(mod, "LEGACY_KEYS", ())}
    old_ns = {ns: (me, mod) for me, mod in plugins for ns in getattr(mod, "LEGACY_NAMESPACES", ())}
    warnings = []
    for src in srcs:
        where = f"{src.name}:pack.toml"
        for key in src.meta.get("extensions", {}):
            if key in owners:
                continue
            if found := legacy.get(key) or old_ns.get(key):
                ns, until = namespace(*found), getattr(found[1], "REMOVED_IN", "a later release")
                old = f"[extensions] `{key}`" if key in legacy else f"[extensions.{key}]"
                warnings.append(f"{where}: {old} is deprecated; move it under [extensions.{ns}] "
                                f"(read until {until})")
            else:
                warnings.append(f"{where}: no enabled pack reads [extensions] `{key}`")
        if src.meta.get("validator") and not src.is_core and not trusted(src):
            warnings.append(f"{where}: ships a validator that brainrc doesn't run; set "
                            f"`run_validator = true` for [{src.key}] in packs.local.toml if you trust it")
    return warnings


def plugin_errors(srcs: list[Source], plugins: list[tuple[Source, ModuleType]]) -> list[str]:
    return [e for me, mod in plugins if hasattr(mod, "check") for e in mod.check(me, srcs)]


def plugin_findings(plugins: list[tuple[Source, ModuleType]]) -> list[tuple[str, str, str]]:
    return [f for me, mod in plugins if hasattr(mod, "doctor") for f in mod.doctor(me)]


def render_extensions(srcs: list[Source]) -> str | None:
    """$BRAINRC_HOME/extensions.md from the first plugin that renders it, or None when none does."""
    for me, mod in validators(srcs):
        if hasattr(mod, "render_extensions"):
            others = [s for s in srcs if not s.is_core and s is not me]
            return mod.render_extensions([(s.name, table(s, me, mod)) for s in others])
    return None
