"""OpenCode agent renders: OpenCode rejects Claude's agent frontmatter."""
from __future__ import annotations

from pathlib import Path

from .config import ConfigError, load_harnesses, rendered_agents_dir
from .sources import Source, frontmatter, markdown_files


AGENT_FORMATS = ("claude", "opencode")  # harnesses.toml `agents_format`; claude links agents as written


# OpenCode permission keys each Claude tool needs. An agent's missing tools become `deny`.
OPENCODE_PERMISSIONS = {
    "Read": ("read", "list"), "Grep": ("grep",), "Glob": ("glob",), "Edit": ("edit",),
    "Write": ("edit",), "MultiEdit": ("edit",), "NotebookEdit": ("edit",), "Bash": ("bash",),
    "WebFetch": ("webfetch",), "WebSearch": ("websearch",), "Task": ("task",),
    "TodoWrite": ("todowrite",),
}


def opencode_agent(path: Path) -> str:
    """An agent in OpenCode's format: OpenCode rejects Claude's `tools: Read, Grep` string. Tools
    the agent lacks become `deny`; the rest are left to the user's own OpenCode permissions.
    `model` is dropped: a subagent then uses the model of the agent that called it."""
    text = path.read_text()
    head, _, body = text.partition("\n---\n")
    keep = [line for line in head.splitlines()[1:] if line.startswith(("name:", "description:"))]
    lines = ["---", *keep, "mode: subagent"]
    tools = frontmatter(path).get("tools")
    if tools is not None:
        allowed = {key for t in tools.split(",") for key in OPENCODE_PERMISSIONS.get(t.strip(), ())}
        denied = sorted({k for keys in OPENCODE_PERMISSIONS.values() for k in keys} - allowed)
        lines += ["permission:", *(f"  {key}: deny" for key in denied)]
    return "\n".join(lines) + "\n---\n" + body


def agents_format(h: dict) -> str:
    fmt = h.get("agents_format", "claude")
    if fmt not in AGENT_FORMATS:
        raise ConfigError(f"harnesses.toml: unknown agents_format `{fmt}` (use one of {', '.join(AGENT_FORMATS)})")
    return fmt


def rendered_agents(srcs: list[Source]) -> dict[Path, str]:
    """OpenCode copies of every agent, when an enabled harness asks for them."""
    if not any(agents_format(h) == "opencode" for h in load_harnesses().values()):
        return {}
    return {rendered_agents_dir() / f.name: opencode_agent(f)
            for src in srcs for f in markdown_files("agents", src)}
