"""Antigravity CLI: its hooks.json keeps each hook set under a name ({"<name>": {"PreToolUse": [...]}}).
brainrc's groups go under ENTRY, and a hook set the user named stays theirs."""
from __future__ import annotations

import copy

from .base import Adapter

ENTRY = "brainrc"


class Antigravity(Adapter):
    name = "antigravity"
    label = "Antigravity CLI"
    settings_format = "antigravity"
    defines_settings_format = True

    def hooks_view(self, current: dict) -> dict:
        entry = current.get(ENTRY)
        return {"hooks": copy.deepcopy(entry)} if isinstance(entry, dict) else {}

    def hooks_put(self, current: dict, merged: dict) -> dict:
        out = copy.deepcopy(current)
        hooks = merged.get("hooks")
        if hooks:
            out[ENTRY] = hooks
        elif isinstance(current.get(ENTRY), dict):
            out.pop(ENTRY)  # brainrc emptied its own entry
        return out

    def hooks_problem(self, current: dict) -> str | None:
        if ENTRY in current and not isinstance(current[ENTRY], dict):
            return f"its `{ENTRY}` entry isn't an object"
        return None
