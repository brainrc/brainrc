"""Kiro (#310): skills, a global steering file, MCP servers and a PreToolUse guard in ~/.kiro.

Kiro's hook files hold a list, {"version": "v1", "hooks": [{"name", "trigger", "matcher",
"action": {"type": "command", "command"}, "timeout"}]}, not Claude Code's map of events. The view
maps each entry to a Claude Code group under its trigger and keeps the entry whole, so one brainrc
didn't write goes back exactly as it was.
"""
from __future__ import annotations

import copy

from .base import Adapter, server_entry

VERSION = "v1"
KEPT = "_kiro"  # the original entry, inside a viewed group


def _group(entry: dict) -> dict:
    action = entry.get("action") if isinstance(entry.get("action"), dict) else {}
    hook = {"type": "command", "command": str(action.get("command", ""))}
    if isinstance(entry.get("timeout"), (int, float)):
        hook["timeout"] = entry["timeout"]
    return {"matcher": entry.get("matcher", "*"), "hooks": [hook], KEPT: entry}


def _entry(trigger: str, group: dict) -> list[dict]:
    if KEPT in group:
        return [group[KEPT]]
    out = []
    for hook in group.get("hooks", []):
        entry = {"name": "brainrc-guard", "trigger": trigger, "matcher": group.get("matcher", "*"),
                 "action": {"type": "command", "command": hook["command"]}}
        if "timeout" in hook:
            entry["timeout"] = hook["timeout"]
        out.append(entry)
    return out


class Kiro(Adapter):
    name = "kiro"
    label = "Kiro"
    settings_format = "kiro"
    defines_settings_format = True
    writes_mcp = True
    mcp_key = "mcpServers"

    def hooks_view(self, current: dict) -> dict:
        view = {k: copy.deepcopy(v) for k, v in current.items() if k not in ("hooks", "version")}
        events: dict[str, list] = {}
        for entry in current.get("hooks") or []:
            events.setdefault(str(entry.get("trigger", "")), []).append(_group(copy.deepcopy(entry)))
        return view | ({"hooks": events} if events else {})

    def hooks_put(self, current: dict, merged: dict) -> dict:
        out = {k: v for k, v in merged.items() if k != "hooks"}
        hooks = [e for trigger, groups in (merged.get("hooks") or {}).items() for g in groups
                 for e in _entry(trigger, g)]
        if hooks:
            return {"version": current.get("version", VERSION), **out, "hooks": hooks}
        # No hooks left: the file is empty, so uninstall can delete it, unless the user keeps more.
        return ({"version": current["version"]} | out) if out and "version" in current else out

    def hooks_problem(self, current: dict) -> str | None:
        hooks = current.get("hooks", [])
        if not isinstance(hooks, list) or not all(isinstance(e, dict) for e in hooks):
            return "its `hooks` isn't a list of hook objects"
        return None

    def mcp_entry(self, server: dict) -> dict:
        # ${VAR} expands only for variables listed in Kiro's "Mcp Approved Env Vars" setting.
        return server_entry(server)
