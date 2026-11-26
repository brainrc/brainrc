"""Cursor: reads skills and hooks as Claude Code writes them (its hooks.json keeps flat entries,
which the merge already handles); its user rules live in its Settings, so there's no instructions file."""
from __future__ import annotations

from .base import Adapter


class Cursor(Adapter):
    name = "cursor"
    label = "Cursor"
    # "On Windows, the desktop app runs hook commands through PowerShell" (https://cursor.com/docs/hooks).
    windows_shell = "powershell"
