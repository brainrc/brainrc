"""GitHub Copilot (#307): the Copilot CLI and VS Code's Copilot agent read the same user folder,
~/.copilot ($COPILOT_HOME): skills, copilot-instructions.md, mcp-config.json and hooks/*.json.

brainrc's guard is its own hook file, hooks/brainrc.json, in the CLI's format: {"version": 1,
"hooks": {"preToolUse": [flat entries]}}. An entry gives its script as `bash` (or `powershell`);
`command` is a fallback Copilot copies to both, and a bash line run by PowerShell would fail, which
Copilot's preToolUse takes as a deny. So brainrc writes `bash`, and the view shows it as Claude
Code's `command` for the merge and doctor; an entry the user wrote with `command` stays as it was.
"""
from __future__ import annotations

import copy

from .base import Adapter, server_entry

AS_BASH = "_copilot_bash"  # a viewed entry whose `command` is its `bash`
AS_COMMAND = "_copilot_command"  # a viewed entry the user wrote with `command`


def _view(entry):
    if not isinstance(entry, dict):
        return entry
    entry = copy.deepcopy(entry)
    if "command" in entry:
        entry[AS_COMMAND] = True
    elif isinstance(entry.get("bash"), str):
        entry = {("command" if k == "bash" else k): v for k, v in entry.items()} | {AS_BASH: True}
    return entry


def _put(entry):
    if not isinstance(entry, dict):
        return entry
    entry = dict(entry)
    entry.pop(AS_BASH, None)
    if not entry.pop(AS_COMMAND, False) and "command" in entry and "bash" not in entry:
        # brainrc's own entries, and those viewed from `bash`: the key renamed where it stands
        entry = {("bash" if k == "command" else k): v for k, v in entry.items()}
    return entry


def _events(hooks, each) -> dict:
    return {event: [each(e) for e in entries] if isinstance(entries, list) else entries
            for event, entries in hooks.items()}


class Copilot(Adapter):
    name = "copilot"
    label = "GitHub Copilot (CLI, VS Code)"
    settings_format = "copilot"
    defines_settings_format = True
    writes_mcp = True
    mcp_key = "mcpServers"

    def hooks_view(self, current: dict) -> dict:
        hooks = current.get("hooks")
        return current | {"hooks": _events(hooks, _view)} if isinstance(hooks, dict) else current

    def hooks_put(self, current: dict, merged: dict) -> dict:
        hooks = merged.get("hooks")
        return merged | {"hooks": _events(hooks, _put)} if isinstance(hooks, dict) else merged

    def mcp_entry(self, server: dict) -> dict:
        kind = {"type": "http" if "url" in server else "stdio"}
        return kind | server_entry(server) | {"tools": ["*"]}
