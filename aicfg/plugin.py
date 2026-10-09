"""Plugin manifests: Claude Code (also read by Codex), Cursor, and Antigravity."""
from __future__ import annotations

import json

from . import config
from .config import ConfigError
from .sources import core_version
from .plan import FragmentError, render_fragment


PLUGIN_DIR = ".claude-plugin"


CURSOR_PLUGIN_DIR = ".cursor-plugin"  # Cursor reads it before .claude-plugin/, whose hooks it rejects


PLUGIN_NAME = "ai-config"


PLUGIN_AUTHOR = {"name": "ai-config contributors"}


PLUGIN_DESCRIPTION = ("Skills, agents, commands, and guard hooks for spec-driven work: spec-agent "
                      "takes a ticket to a reviewed PR through approval gates.")


def plugin_manifests() -> dict[str, str]:
    """The plugin manifests for core, built from the repo: Claude Code's plugin and marketplace
    (Codex reads them too), Cursor's plugin, and Antigravity's root plugin.json. The repo root is
    the plugin."""
    version = ".".join(map(str, core_version()))
    hooks_dir = "${CLAUDE_PLUGIN_ROOT}/overrides/claude/hooks"
    hooks = render_fragment(config.REPO / "overrides" / "claude" / "settings.fragment.json", hooks_dir)["hooks"]
    plugin = {"name": PLUGIN_NAME, "version": version, "description": PLUGIN_DESCRIPTION,
              "author": PLUGIN_AUTHOR, "license": "MIT", "hooks": hooks}
    market = {"name": PLUGIN_NAME, "owner": PLUGIN_AUTHOR, "description": PLUGIN_DESCRIPTION,
              "plugins": [{"name": PLUGIN_NAME, "source": ".", "description": PLUGIN_DESCRIPTION,
                           "version": version}]}
    manifests = {f"{PLUGIN_DIR}/{name}": json.dumps(data, indent=2) + "\n"
                 for name, data in (("plugin.json", plugin), ("marketplace.json", market))}
    cursor_hooks = render_fragment(config.REPO / "overrides" / "cursor" / "settings.fragment.json",
                                   "${CURSOR_PLUGIN_ROOT}/overrides/cursor/hooks")
    cursor = {"name": PLUGIN_NAME, "version": version, "description": PLUGIN_DESCRIPTION,
              "author": PLUGIN_AUTHOR, "license": "MIT", "skills": "./skills/", "agents": "./agents/",
              "rules": "./rules/", "hooks": f"./{CURSOR_PLUGIN_DIR}/hooks.json"}  # a file, as Cursor's own plugins do
    manifests[f"{CURSOR_PLUGIN_DIR}/plugin.json"] = json.dumps(cursor, indent=2) + "\n"
    manifests[f"{CURSOR_PLUGIN_DIR}/hooks.json"] = json.dumps(cursor_hooks, indent=2) + "\n"
    manifests["plugin.json"] = json.dumps({"name": PLUGIN_NAME}, indent=2) + "\n"  # Antigravity
    return manifests


def check_plugin() -> list[str]:
    """Only where the repo publishes a plugin (has .claude-plugin/), as core does."""
    if not (config.REPO / PLUGIN_DIR).is_dir():
        return []
    try:
        manifests = plugin_manifests()
    except FragmentError:
        return []  # validate reports the fragment itself
    errors = []
    for rel, text in manifests.items():
        path = config.REPO / rel
        if not path.is_file():
            errors.append(f"{rel}: missing; run `python3 scripts/aicfg.py plugin`")
        elif path.read_text() != text:
            errors.append(f"{rel}: stale (VERSION, hooks, or the fragment changed); "
                          "run `python3 scripts/aicfg.py plugin`")
    return errors


def cmd_plugin() -> int:
    """Write the plugin manifests; they're committed so GitHub installs work."""
    if config.installed():
        print("ERROR plugin writes the repo's manifests; run it from a checkout: "
              "python3 scripts/aicfg.py plugin")
        return 1
    try:
        manifests = plugin_manifests()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    changed = False
    for rel, text in manifests.items():
        path = config.REPO / rel
        if path.is_file() and path.read_text() == text:
            continue
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
        print(f"WROTE {rel}")
        changed = True
    if not changed:
        print("Plugin manifests up to date.")
    return 0
