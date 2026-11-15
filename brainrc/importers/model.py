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

    def unique(self, slug: str) -> str:
        """slug, or slug-2, -3... when this source already has a rule or skill of that name."""
        taken = {s.slug for s in self.skills} | {r.slug for r in self.rules}
        name, n = slug, 2
        while name in taken:
            name, n = f"{slug}-{n}", n + 1
        return name

    def add_skill(self, slug: str, description: str, scoped: list[str], body: str, provenance: str,
                  label: str, manual: str) -> None:
        """A rule another tool loads only for some files, or on request, as a skill. Scoped by
        globs: its description says so and a Domains row names it. Neither globs nor a
        description: `manual` becomes its description, and a warning says it loads only on request."""
        if scoped:
            where = ", ".join(f"`{g}`" for g in scoped)
            description = (f"{description.rstrip('.')}. " if description else "") + f"Use when working on {where}."
            self.domains.append({"files": where, "skills": [slug]})
        elif not description:
            description = manual
            self.warnings.append(f"{label}: has no description or file globs, so it becomes a skill the "
                                 "model loads only when asked")
        self.skills.append(Skill(slug, description, body, provenance))
