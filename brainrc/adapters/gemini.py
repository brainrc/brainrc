"""Gemini CLI: retired in favour of Antigravity CLI, and off by default in harnesses.toml."""
from __future__ import annotations

from .base import Adapter


class Gemini(Adapter):
    name = "gemini"
    label = "Gemini CLI"
