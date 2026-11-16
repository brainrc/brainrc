"""What an importer returns: the rules, skills and Domains rows one source becomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..scaffold import Rule, Skill


@dataclass
class Imported:
    rules: list[Rule] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    domains: list[dict] = field(default_factory=list)  # {"files": "`glob`", "skills": [slug, ...]}
    warnings: list[str] = field(default_factory=list)
    read: set[Path] = field(default_factory=set)  # every file read, inlined ones too (resolved)
