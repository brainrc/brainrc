"""The capability matrix (#298): which content reaches each tool, generated from harnesses.toml.

docs/capabilities.md holds the table between two marker lines; `brainrc capabilities --write`
rewrites it, and tests/test_capabilities.py fails when the page and harnesses.toml disagree.
"""
import json
from pathlib import Path

from . import config
from .config import ConfigError

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
    return f"`{config.env_default(h[key], defaults=True)}`" if key in h else NONE


def _hooks(root: Path, name: str, h: dict) -> str:
    if "plugin" in h:
        return f"plugin {_path(h, 'plugin')}"
    if "settings" not in h:
        return NONE
    fragment = root / "overrides" / name / "settings.fragment.json"
    events = sorted(json.loads(fragment.read_text(encoding="utf-8")).get("hooks", {})) if fragment.is_file() else []
    return f"{_path(h, 'settings')}: {', '.join(events)}" if events else NONE


def _repo(h: dict) -> str:
    """Project scope always writes the standard files; project_* adds a tool's own (docs/project.md)."""
    out = ["`.agents/skills/`", "`AGENTS.md`"]
    if "project_skills" in h:
        out.append(f"`{h['project_skills']}/` (copy)")
    if "project_instructions" in h:
        out.append(f"`{h['project_instructions']}` (imports AGENTS.md)")
    return ", ".join(out)


def _row(root: Path, name: str, h: dict) -> list[str]:
    label = LABELS.get(name, name) + ("" if h.get("enabled", True) else " (off by default)")
    agents = _path(h, "agents") + (" (rendered)" if h.get("agents_format") == "opencode" else "")
    return [label, _path(h, "skills"), _path(h, "instructions"), agents if "agents" in h else NONE,
            _path(h, "commands"), _hooks(root, name, h), _path(h, "mcp"), _repo(h),
            ", ".join(f"`{v}`" for v in config.env_vars(h)) or NONE]


def render(root: Path | None = None) -> str:
    """The table for root's harnesses.toml (the shipped file, never the local one). Raises
    ConfigError for a broken file."""
    root = root or config.REPO
    harnesses = config._read_toml(root / "harnesses.toml")
    rows = [COLUMNS, ["---"] * len(COLUMNS)] + [_row(root, n, h) for n, h in harnesses.items()]
    return "\n".join("| " + " | ".join(r) + " |" for r in rows)


def _parts(text: str) -> tuple[str, str, str] | None:
    """The page split into (before BEGIN, the table, from END on), or None without both markers."""
    head, begin, rest = text.partition(BEGIN)
    table, end, tail = rest.partition(END)
    return (head, table.strip(), end + tail) if begin and end else None


def current(text: str) -> str | None:
    """The table between the markers in the page's text, or None when a marker is missing."""
    parts = _parts(text)
    return parts[1] if parts else None


def write(root: Path | None = None) -> bool:
    """Rewrite the page's table from harnesses.toml; True if it changed. Raises ConfigError."""
    root = root or config.REPO
    page = root / PAGE
    text = page.read_text(encoding="utf-8")
    parts = _parts(text)
    if parts is None:
        raise ConfigError(f"{PAGE}: the BEGIN and END capability matrix marker lines are missing")
    new = f"{parts[0]}{BEGIN}\n{render(root)}\n{parts[2]}"
    changed = new != text
    if changed:
        page.write_text(new, encoding="utf-8")
    return changed


def cmd_capabilities(write_page: bool) -> int:
    """Print the matrix, or with write_page rewrite docs/capabilities.md (from a checkout only)."""
    if write_page and config.installed():
        print(f"ERROR capabilities --write writes the repo's {PAGE}; run it from a checkout: "
              "python3 scripts/brainrc.py capabilities --write")
        return 1
    try:
        if write_page:
            print(f"{PAGE}: {'updated' if write() else 'up to date'}")
        else:
            print(render())
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    return 0
