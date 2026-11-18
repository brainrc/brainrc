"""A Claude Code plugin (#167): a folder with `.claude-plugin/plugin.json`, and its skills, agents,
commands, hooks and MCP servers.

- `skills/<name>/` becomes `skills/<prefix><name>/`, every file in it kept; agents and commands get
  the prefix too. Each keeps its frontmatter but `name`, which becomes the pack's name for it, and
  its text names the pack's items where it named the plugin's (`/plugin:skill`, `[agent: x]`).
- `hooks/hooks.json` (or plugin.json's `hooks`) becomes `overrides/claude/settings.fragment.json`.
  `${CLAUDE_PLUGIN_ROOT}/hooks/x` becomes `{{hooks_dir}}/x`, and the files hook commands run are
  copied into `overrides/claude/hooks/`, which apply links as the pack's hooks folder.
- `.mcp.json` (or plugin.json's `mcpServers`) becomes `mcp/servers.toml`, with the prefix on each
  server's name. An `env` value that is `${NAME}` becomes `env_from = ["NAME"]`; any other value
  is left out with a warning, since brainrc never writes one. A server that runs the plugin's
  own files is left out with a warning too: they have nowhere to go.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..config import tilde
from ..scaffold import Agent, Command, Copied, Skill, slugify
from ..sources import parse_frontmatter
from .model import Imported

NAMES = ("plugin.json",)
LOOK_FOR = (".claude-plugin",)
ROOT_VAR = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}|\$CLAUDE_PLUGIN_ROOT\b")
ROOT_PATH = re.compile(r"(?:\$\{CLAUDE_PLUGIN_ROOT\}|\$CLAUDE_PLUGIN_ROOT\b)/?([^\s\"';|&)<>]*)")
ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
HOOKS = "overrides/claude/hooks"


def detect(path: Path) -> bool:
    if path.is_file():
        return path.name == "plugin.json" and path.parent.name == ".claude-plugin"
    return path.is_dir() and path.name == ".claude-plugin" and (path / "plugin.json").is_file()


def _content(path: Path) -> Copied:
    """The file byte for byte (line ends included), and whether it is executable."""
    return Copied(path.read_bytes(), bool(path.stat().st_mode & 0o111))


def _tree(root: Path, out: Imported) -> dict[str, Copied]:
    """Every file under root, by its path in root, in path order; links are skipped with a warning."""
    found = {}
    for p in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = p.relative_to(root)
        if set(rel.parts) & SKIP_DIRS:
            continue
        if p.is_symlink():
            out.warnings.append(f"{tilde(p)}: a link; not imported (copy what it points at into the pack)")
        elif p.is_file():
            found[rel.as_posix()] = _content(p)
            out.read.add(p.resolve())
    return found


def _split(text: str) -> tuple[list[tuple[str, list[str]]], str, int]:
    """A markdown file's frontmatter as (key, its lines as written) in order, the body, and the
    body's first line number."""
    lines = text.splitlines()
    _, start = parse_frontmatter(lines)
    if not start:
        return [], text, 1
    fields: list[tuple[str, list[str]]] = []
    for line in lines[1:start - 1]:
        m = re.match(r"([A-Za-z0-9_-]+)\s*:", line)
        if m and not line[:1].isspace():
            fields.append((m[1], [line]))
        elif fields:
            fields[-1][1].append(line)  # an indented or block-scalar line belongs to the key above
    body = "\n".join(lines[start:]).strip("\n")
    lead = next((i for i in range(start, len(lines)) if lines[i].strip()), start)
    return fields, body, lead + 1


def _item(path: Path, label: str, agent: bool = False):
    """(frontmatter values, the other frontmatter lines, body, provenance) of one item file. An
    agent's `tools` and `model` are written by agent_text, so they aren't among the other lines."""
    text = path.read_text(encoding="utf-8-sig")
    meta, _ = parse_frontmatter(text.splitlines())
    fields, body, first = _split(text)
    own = ("name", "description", "tools", "model") if agent else ("name", "description")
    extra = [line for key, lines in fields if key not in own for line in lines]
    last = len(text.rstrip().splitlines())
    return meta, extra, body, f"imported by brainrc from {label}, lines {first}-{last}"


def _paths(root: Path, manifest: dict, key: str, default: str) -> list[Path]:
    """The default folder and any paths plugin.json adds under key (a string or a list of them)."""
    extra = manifest.get(key, [])
    extra = [extra] if isinstance(extra, str) else extra if isinstance(extra, list) else []
    found = [root / default] + [root / e for e in extra if isinstance(e, str)]
    return list(dict.fromkeys(p for p in found if p.exists() and p.resolve().is_relative_to(root.resolve())))


def _md_files(paths: list[Path]) -> list[Path]:
    out = []
    for p in paths:
        out += [p] if p.is_file() else sorted(f for f in p.glob("*.md") if f.is_file() and f.name != "README.md")
    return out


def _skills(root: Path, manifest: dict, out: Imported) -> None:
    olds = out.renames.setdefault("skills", {})
    for folder in _paths(root, manifest, "skills", "skills"):
        dirs = [folder] if (folder / "SKILL.md").is_file() else sorted(
            d for d in folder.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
        for d in dirs:
            if d.is_symlink():
                out.warnings.append(f"{tilde(d)}: a link; not imported")
                continue
            label = tilde(d / "SKILL.md")
            meta, extra, body, provenance = _item(d / "SKILL.md", label)
            name = meta.get("name") or d.name
            slug = out.unique(slugify(name, "skill"))
            files = _tree(d, out)
            files.pop("SKILL.md", None)
            if not meta.get("description"):
                out.warnings.append(f"{label}: no description; add one, or the skill never loads on its own")
            out.skills.append(Skill(slug, meta.get("description") or f"The plugin skill `{name}`.", body,
                                    provenance, extra=extra, files=files))
            olds.setdefault(name, slug)
            olds.setdefault(d.name, slug)


def _agents_and_commands(root: Path, manifest: dict, out: Imported) -> None:
    for kind in ("agents", "commands"):
        olds = out.renames.setdefault(kind, {})
        used: set[str] = set()
        for f in _md_files(_paths(root, manifest, kind, kind)):
            out.read.add(f.resolve())
            label = tilde(f)
            meta, extra, body, provenance = _item(f, label, agent=kind == "agents")
            name = (meta.get("name") or f.stem) if kind == "agents" else f.stem  # a command is its file's name
            base = slug = slugify(name, kind[:-1])
            n = 2
            while slug in used:
                slug, n = f"{base}-{n}", n + 1
            used.add(slug)
            description = meta.get("description", "")
            if not description:
                out.warnings.append(f"{label}: no description; validate needs one")
                description = f"The plugin {kind[:-1]} `{name}`."
            if kind == "agents":
                tools = meta.get("tools", "").strip()
                tools = tools[1:-1] if tools.startswith("[") and tools.endswith("]") else tools  # a flow list
                out.agents.append(Agent(slug, description, body, provenance,
                                        tools=", ".join(t.strip(" '\"") for t in tools.split(",") if t.strip()),
                                        model=meta.get("model", ""), extra=extra))
            else:
                out.commands.append(Command(slug, description, body, provenance, extra=extra))
            olds.setdefault(name, slug)  # the plugin's name means the first item that has it


def _load_json(path: Path, out: Imported) -> dict:
    out.read.add(path.resolve())
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        out.warnings.append(f"{tilde(path)}: not valid JSON ({e.msg}, line {e.lineno}); skipped")
        return {}
    if not isinstance(data, dict):
        out.warnings.append(f"{tilde(path)}: not a JSON object; skipped")
        return {}
    return data


def _hook_source(root: Path, manifest: dict, out: Imported) -> list[tuple[str, dict]]:
    """(label, hooks object) for each hooks config: plugin.json's `hooks` (an object, or paths to
    files), else hooks/hooks.json."""
    given = manifest.get("hooks")
    if isinstance(given, dict):
        return [(tilde(root / ".claude-plugin/plugin.json"), given)]
    paths = [given] if isinstance(given, str) else given if isinstance(given, list) else ["hooks/hooks.json"]
    found = []
    for rel in paths:
        path = root / rel
        if isinstance(rel, str) and path.is_file() and path.resolve().is_relative_to(root.resolve()):
            data = _load_json(path, out)
            hooks = data.get("hooks", data) if data else {}
            if isinstance(hooks, dict):
                found.append((tilde(path), hooks))
    return found


def _hooks(root: Path, manifest: dict, out: Imported) -> None:
    copied: set[str] = set()

    def place(m: re.Match) -> str:
        rel = m[1].strip("/")
        if not rel:
            out.warnings.append(f"{label}: a hook runs `${{CLAUDE_PLUGIN_ROOT}}` itself; it now names the "
                                "pack's hooks folder, check it")
            return "{{hooks_dir}}"
        inside = rel.removeprefix("hooks/") if rel.startswith("hooks/") else rel
        top = rel.split("/")[0]
        if top not in copied and (root / top).exists() and (root / top).resolve().is_relative_to(root.resolve()):
            copied.add(top)
            if (root / top).is_dir():
                for sub, data in _tree(root / top, out).items():
                    dest = sub if top == "hooks" else f"{top}/{sub}"
                    if top == "hooks" and sub == "hooks.json":
                        continue
                    out.pack_files[f"{HOOKS}/{dest}"] = data
            else:
                out.read.add((root / top).resolve())
                out.pack_files[f"{HOOKS}/{top}"] = _content(root / top)
        elif not (root / rel).exists():
            out.warnings.append(f"{label}: a hook runs {rel}, which the plugin doesn't have")
        return "{{hooks_dir}}/" + inside

    def walk(value):
        if isinstance(value, str):
            return ROOT_PATH.sub(place, value)
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for label, hooks in _hook_source(root, manifest, out):
        for event, groups in hooks.items():
            if not isinstance(groups, list):
                out.warnings.append(f"{label}: hooks `{event}` is not a list; skipped")
                continue
            for group in walk(groups):
                kept = _owned_hooks(group, f"{label}: a `{event}` hook", out)
                if kept:
                    out.hooks.setdefault(event, []).append(kept)


def _owned_hooks(group, where: str, out: Imported) -> dict | None:
    """group with only the hooks that run a file in the pack. apply knows a hook is the pack's by
    `{{hooks_dir}}` in its command; any other (`npx prettier`, a prompt hook) would be added again
    on every apply and never removed, so it is left out with a warning."""
    if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
        out.warnings.append(f"{where}: not a matcher group with a `hooks` list; skipped")
        return None
    hooks = []
    for h in group["hooks"]:
        command = h.get("command", "") if isinstance(h, dict) else ""
        if isinstance(command, str) and "{{hooks_dir}}" in command:
            hooks.append(h)
        else:
            what = f"`{command}`" if command else f"a `{h.get('type', '?') if isinstance(h, dict) else '?'}` hook"
            out.warnings.append(f"{where} runs {what}, not a file of the plugin's; left out. To keep it, "
                                "put it in a script in overrides/claude/hooks/ and run that as "
                                "{{hooks_dir}}/<script> in settings.fragment.json")
    return {**group, "hooks": hooks} if hooks else None


def _servers(root: Path, manifest: dict, out: Imported) -> None:
    given = manifest.get("mcpServers")
    if isinstance(given, dict):
        label, servers = tilde(root / ".claude-plugin/plugin.json"), given
    else:
        path = root / (given if isinstance(given, str) else ".mcp.json")
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            return
        label, data = tilde(path), _load_json(path, out)
        servers = data.get("mcpServers", data) if data else {}
    if not isinstance(servers, dict):
        out.warnings.append(f"{label}: `mcpServers` is not an object; skipped")
        return
    for name, server in servers.items():
        where = f"{label}: server `{name}`"
        if not isinstance(server, dict):
            out.warnings.append(f"{where}: not an object; skipped")
            continue
        if ROOT_VAR.search(json.dumps(server)):
            out.warnings.append(f"{where} runs the plugin's own files (${{CLAUDE_PLUGIN_ROOT}}); not imported. "
                                "Install them somewhere and add the server to mcp/servers.toml by hand")
            continue
        table: dict = {}
        if server.get("url"):
            table["url"] = str(server["url"])
            if server.get("headers"):
                out.warnings.append(f"{where}: its `headers` are left out; mcp/servers.toml has no headers")
        elif server.get("command"):
            table["command"] = str(server["command"])
            if server.get("args"):
                table["args"] = [str(a) for a in server["args"]]
        else:
            out.warnings.append(f"{where}: no `command` or `url`; skipped")
            continue
        env_from = []
        for key, value in (server.get("env") or {}).items():
            m = ENV_REF.fullmatch(str(value).strip())
            if m and (m[1] or m[2]) == key:
                env_from.append(key)
            else:
                out.warnings.append(f"{where}: env `{key}` is left out: brainrc writes variable names, never "
                                    f"values; set {key} in your environment and add it to `env_from`")
        if env_from and "url" in table:
            out.warnings.append(f"{where}: an HTTP server takes no `env`; {', '.join(env_from)} left out")
        elif env_from:
            table["env_from"] = env_from
        if any(ENV_REF.search(a) for a in table.get("args", [])) or ENV_REF.search(table.get("url", "")):
            out.warnings.append(f"{where}: `$VARIABLE`s in its args or url are passed as written; not every "
                                "tool expands them")
        base = slug = slugify(name, "server")
        n = 2
        while slug in out.servers:
            slug, n = f"{base}-{n}", n + 1
        if slug != base:
            out.warnings.append(f"{where}: another server is also `{base}`; this one is `{slug}`")
        out.servers[slug] = table
        out.server_names[name] = slug


def read(path: Path) -> Imported:
    out = Imported()
    folder = path if path.is_dir() else path.parent
    root = folder.parent  # the plugin's own folder holds .claude-plugin/
    manifest = _load_json(folder / "plugin.json", out)
    out.namespace = str(manifest.get("name", "")) if manifest else ""
    _skills(root, manifest, out)
    _agents_and_commands(root, manifest, out)
    _hooks(root, manifest, out)
    _servers(root, manifest, out)
    if not (out.skills or out.agents or out.commands or out.hooks or out.servers):
        out.warnings.append(f"{tilde(root)}: the plugin has no skills, agents, commands, hooks or MCP servers")
    return out
