"""Plugin manifests: Claude Code (also read by Codex), Cursor, and Antigravity; and the root
package.json that `npx github:brainrc/brainrc` installs."""
from __future__ import annotations

import json

from . import config
from .config import ConfigError
from .sources import core_version
from .plan import FragmentError, render_fragment


PLUGIN_DIR = ".claude-plugin"


CURSOR_PLUGIN_DIR = ".cursor-plugin"  # Cursor reportedly falls back to .claude-plugin/, whose hooks it rejects


PLUGIN_NAME = "brainrc"


PLUGIN_AUTHOR = {"name": "brainrc contributors"}


PLUGIN_DESCRIPTION = ("Guard hooks for AI coding harnesses. Gatework, the spec-driven skills and agents, "
                      "is its own plugin: brainrc/gatework.")


NPX_SHIM = "bin/brainrc.js"


def npm_package(version: str) -> dict:
    """package.json for `npx github:brainrc/brainrc` (#278): the shim and VERSION only. `private`
    keeps it off npm, which brainrc doesn't publish to; the shim runs the PyPI release at `version`."""
    return {"name": PLUGIN_NAME, "version": version,
            "description": "Runs brainrc (a Python CLI, from PyPI) through uv: npx github:brainrc/brainrc",
            "license": "MIT", "private": True,
            "repository": {"type": "git", "url": "git+https://github.com/brainrc/brainrc.git"},
            "bin": {PLUGIN_NAME: NPX_SHIM}, "files": [NPX_SHIM, "VERSION"], "engines": {"node": ">=18"}}


def plugin_manifests() -> dict[str, str]:
    """The plugin manifests for core, built from the repo: Claude Code's plugin and marketplace
    (Codex reads them too), Cursor's plugin, and Antigravity's root plugin.json. The repo root is
    the plugin. Core ships no skills or agents: Gatework's are in its own repo and plugin."""
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
              "author": PLUGIN_AUTHOR, "license": "MIT",
              "rules": "./rules/", "hooks": f"./{CURSOR_PLUGIN_DIR}/hooks.json"}  # a file, as Cursor's own plugins do
    manifests[f"{CURSOR_PLUGIN_DIR}/plugin.json"] = json.dumps(cursor, indent=2) + "\n"
    manifests[f"{CURSOR_PLUGIN_DIR}/hooks.json"] = json.dumps(cursor_hooks, indent=2) + "\n"
    # Antigravity loads `rules/` and `skills/` at the root; its schema requires `name` and rejects unknown keys.
    manifests["plugin.json"] = json.dumps({"name": PLUGIN_NAME}, indent=2) + "\n"
    if (config.REPO / NPX_SHIM).is_file():  # core has the shim; a pack that publishes a plugin doesn't
        manifests["package.json"] = json.dumps(npm_package(version), indent=2) + "\n"
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
            errors.append(f"{rel}: missing; run `python3 scripts/brainrc.py plugin`")
        elif path.read_text() != text:
            errors.append(f"{rel}: stale (VERSION, hooks, or the fragment changed); "
                          "run `python3 scripts/brainrc.py plugin`")
    return errors


def cmd_plugin() -> int:
    """Write the plugin manifests; they're committed so GitHub installs work."""
    if config.installed():
        print("ERROR plugin writes the repo's manifests; run it from a checkout: "
              "python3 scripts/brainrc.py plugin")
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
