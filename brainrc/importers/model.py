"""What an importer returns: the rules, skills, agents, commands, MCP servers, hooks and Domains rows
one source becomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..config import tilde
from ..scaffold import Agent, Command, Copied, Rule, Skill


@dataclass
class Imported:
    rules: list[Rule] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    domains: list[dict] = field(default_factory=list)  # {"files": "`glob`", "skills": [slug, ...]}
    warnings: list[str] = field(default_factory=list)
    read: set[Path] = field(default_factory=set)  # every file read, inlined ones too (resolved)
    agents: list[Agent] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)
    servers: dict[str, dict] = field(default_factory=dict)  # mcp/servers.toml tables, by name after the prefix
    hooks: dict[str, list] = field(default_factory=dict)  # Claude Code hook event -> its matcher groups
    pack_files: dict[str, Copied] = field(default_factory=dict)  # other pack files (hook scripts), by path
    server_names: dict[str, str] = field(default_factory=dict)  # a server's name in the source -> its slug
    # The source's own names for its skills and agents, which plan rewrites to the pack's names in
    # their text: `[agent: old]`, "`old` skill", and `namespace:old` (a plugin's `/plugin:skill`).
    renames: dict[str, dict[str, str]] = field(default_factory=dict)  # "skills"|"agents" -> {old: slug}
    namespace: str = ""

    def unique(self, slug: str) -> str:
        """slug, or slug-2, -3... when this source already has a rule or skill of that name."""
        taken = {s.slug for s in self.skills} | {r.slug for r in self.rules}
        name, n = slug, 2
        while name in taken:
            name, n = f"{slug}-{n}", n + 1
        return name

    def files(self, path: Path, suffix: str) -> list[Path]:
        """path, or the files under it that end in suffix in path order (the tools' own order),
        each recorded as read; a warning when a folder has none."""
        found = [path] if path.is_file() else sorted(
            (f for f in path.rglob(f"*{suffix}") if f.is_file()), key=lambda f: f.relative_to(path).as_posix())
        self.read |= {f.resolve() for f in found}
        if not found:
            self.warnings.append(f"{tilde(path)}: no {suffix} files")
        return found

    def add_skill(self, slug: str, description: str, scoped: list[str], body: str, provenance: str,
                  label: str, manual: str, missing: str) -> None:
        """A rule another tool loads only for some files, or on request, as a skill. Scoped by
        globs: its description says so and a Domains row names it. Neither globs nor a
        description: `manual` becomes its description, and a warning says it loads only on request."""
        if scoped:
            where = ", ".join(f"`{g}`" for g in scoped)
            description = (f"{description.rstrip('.')}. " if description else "") + f"Use when working on {where}."
            self.domains.append({"files": where, "skills": [slug]})
        elif not description:
            description = manual
            self.warnings.append(f"{label}: has no {missing}, so it becomes a skill the model loads only "
                                 "when asked")
        self.skills.append(Skill(slug, description, body, provenance))
