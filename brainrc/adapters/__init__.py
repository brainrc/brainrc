"""One adapter per AI tool (#306), behind the interface in base.py.

`get(name)` is the adapter for a harnesses.toml table: a shipped one (BUILTIN), one a Python
package adds through the `brainrc.adapters` entry point group, or Plain for a table the user made
up. Format keys in a harness table (`agents_format`, `settings_format`) name the adapter whose
format to use, so a user's own harness can borrow one.
"""
from __future__ import annotations

from importlib import metadata

from ..config import ConfigError
from .amp import Amp
from .antigravity import Antigravity
from .base import Adapter, Plain
from .claude import Claude
from .codex import Codex
from .copilot import Copilot
from .cursor import Cursor
from .devin import Devin
from .gemini import Gemini
from .junie import Junie
from .kiro import Kiro
from .opencode import OpenCode

ENTRY_POINTS = "brainrc.adapters"
# The tools brainrc ships, in harnesses.toml's order.
BUILTIN: dict[str, Adapter] = {a.name: a for a in (Claude(), Codex(), OpenCode(), Antigravity(), Gemini(), Cursor(),
                                                     Copilot(), Devin(), Kiro(), Amp(), Junie())}
# The formats harnesses.toml can name: "claude" (as written), then each shipped adapter's own.
AGENT_FORMATS = ("claude", *(n for n, a in BUILTIN.items() if a.defines_agents_format))
SETTINGS_FORMATS = ("claude", *(n for n, a in BUILTIN.items() if a.defines_settings_format))

_plugins: dict[str, Adapter] | None = None


def _load(ep) -> Adapter:
    try:
        obj = ep.load()
        adapter = obj() if isinstance(obj, type) else obj
    except Exception as e:  # a broken package must say which one, not crash apply
        raise ConfigError(f"adapter `{ep.name}` ({ep.value}): can't load it: {e}") from None
    if not isinstance(adapter, Adapter):
        raise ConfigError(f"adapter `{ep.name}` ({ep.value}) isn't a brainrc.adapters.Adapter")
    if adapter.name != ep.name:
        raise ConfigError(f"adapter `{ep.name}` ({ep.value}) names itself `{adapter.name}`; "
                          "the entry point's name and the adapter's `name` must match")
    return adapter


def plugins() -> dict[str, Adapter]:
    """Adapters installed packages add, by name; a shipped tool's name stays the shipped adapter's."""
    global _plugins
    if _plugins is None:
        found = {}
        for ep in metadata.entry_points(group=ENTRY_POINTS):
            if ep.name not in BUILTIN and ep.name not in found:
                found[ep.name] = _load(ep)
        _plugins = found
    return _plugins


def reset() -> None:
    """Forget the loaded plugins, so the next call reads the entry points again (tests)."""
    global _plugins
    _plugins = None


def every() -> dict[str, Adapter]:
    return {**BUILTIN, **plugins()}


def get(name: str) -> Adapter:
    """The adapter for harness `name`; Plain when no adapter claims it."""
    return BUILTIN.get(name) or plugins().get(name) or Plain(name)


def formats(kind: str) -> tuple[str, ...]:
    """Every agents or settings format, a package adapter's included."""
    flag = f"defines_{kind}_format"
    return ("claude", *(n for n, a in every().items() if getattr(a, flag)))


def agents_format(name: str, h: dict) -> str:
    """The agent format harness `name` uses: its table's `agents_format`, else its adapter's."""
    fmt = h.get("agents_format", get(name).agents_format)
    if fmt not in formats("agents"):
        raise ConfigError(f"harnesses.toml: unknown agents_format `{fmt}` (use one of {', '.join(formats('agents'))})")
    return fmt


def settings_format(name: str, h: dict) -> str:
    """The settings format harness `name` uses: its table's `settings_format`, else its adapter's."""
    fmt = h.get("settings_format", get(name).settings_format)
    if fmt not in formats("settings"):
        raise ConfigError(f"harnesses.toml: unknown settings_format `{fmt}` (use one of {', '.join(formats('settings'))})")
    return fmt


def agent_renderer(name: str, h: dict) -> Adapter | None:
    """The adapter that renders harness `name`'s agents, or None when they're linked as written."""
    fmt = agents_format(name, h)
    return None if fmt == "claude" else get(fmt)


def settings_adapter(fmt: str) -> Adapter:
    """The adapter whose hooks_view and hooks_put handle settings format fmt."""
    return Adapter() if fmt == "claude" else get(fmt)


__all__ = ["Adapter", "Plain", "BUILTIN", "AGENT_FORMATS", "SETTINGS_FORMATS", "ENTRY_POINTS", "get", "every",
           "plugins", "reset", "formats", "agents_format", "settings_format", "agent_renderer", "settings_adapter"]
