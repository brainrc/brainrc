"""The capability matrix (#298): which content reaches each tool, generated from harnesses.toml.

docs/capabilities.md holds the table between two marker lines; `brainrc capabilities --write`
rewrites it, and tests/test_capabilities.py fails when the page and harnesses.toml disagree.
"""
import json
from pathlib import Path

from . import config

PAGE = "docs/capabilities.md"
BEGIN = "<!-- BEGIN capability matrix: generated from harnesses.toml by `brainrc capabilities --write` -->"
END = "<!-- END capability matrix -->"
# How each harness table is named in prose; a harness missing here shows its table name.
LABELS = {"claude": "Claude Code", "codex": "Codex", "opencode": "OpenCode",
          "antigravity": "Antigravity CLI", "gemini": "Gemini CLI", "cursor": "Cursor"}
COLUMNS = ("Tool", "Skills", "Rules", "Agents", "Commands", "Guard hooks", "MCP servers", "In a repo",
           "Moves with")
NONE = "—"


def _path(h: dict, key: str) -> str:
    return f"`{config.env_default(h[key], defaults=True)}`"


def _hooks(root: Path, name: str, h: dict) -> str:
    if "plugin" in h:
        return f"plugin {_path(h, 'plugin')}"
    if "settings" not in h:
        return NONE
    fragment = root / "overrides" / name / "settings.fragment.json"
    events = sorted(json.loads(fragment.read_text()).get("hooks", {})) if fragment.is_file() else []
    return f"{_path(h, 'settings')}: {', '.join(events)}" if events else NONE


def _repo(h: dict) -> str:
    skills = f"`{h['project_skills']}/` (copy)" if "project_skills" in h else "`.agents/skills/`"
    rules = f"`{h['project_instructions']}` (imports AGENTS.md)" if "project_instructions" in h else "`AGENTS.md`"
    return f"{skills}, {rules}"


def _row(root: Path, name: str, h: dict) -> list[str]:
    label = LABELS.get(name, name) + ("" if h.get("enabled", True) else " (off by default)")
    agents = _path(h, "agents") + (" (rendered)" if h.get("agents_format") == "opencode" else "") \
        if "agents" in h else NONE
    moves = sorted({m[1] for k, v in h.items() if k in config.PATH_KEYS and isinstance(v, str)
                    for m in config.ENV_DEFAULT.finditer(v)})
    return [label,
            _path(h, "skills") if "skills" in h else NONE,
            _path(h, "instructions") if "instructions" in h else NONE,
            agents,
            _path(h, "commands") if "commands" in h else NONE,
            _hooks(root, name, h),
            _path(h, "mcp") if "mcp" in h else NONE,
            _repo(h) if h.get("enabled", True) else NONE,
            ", ".join(f"`{v}`" for v in moves) or NONE]


def render(root: Path | None = None) -> str:
    """The table for root's harnesses.toml (the shipped file, never the local one)."""
    import tomllib  # here, not at the top: an old Python gets cli's version message first

    root = root or config.REPO
    harnesses = tomllib.loads((root / "harnesses.toml").read_text())
    rows = [COLUMNS, ["---"] * len(COLUMNS)] + [_row(root, n, h) for n, h in harnesses.items()]
    return "\n".join("| " + " | ".join(r) + " |" for r in rows)


def current(text: str) -> str | None:
    """The table between the markers in the page's text, or None when a marker is missing."""
    if BEGIN not in text or END not in text:
        return None
    return text.split(BEGIN, 1)[1].split(END, 1)[0].strip()


def write(root: Path | None = None) -> bool:
    """Rewrite the page's table from harnesses.toml; True if it changed."""
    root = root or config.REPO
    page = root / PAGE
    text = page.read_text()
    if current(text) is None:
        raise SystemExit(f"{PAGE}: the {BEGIN!r} and {END!r} lines are missing")
    head, rest = text.split(BEGIN, 1)
    new = f"{head}{BEGIN}\n{render(root)}\n{END}{rest.split(END, 1)[1]}"
    if new != text:
        page.write_text(new)
    return new != text
