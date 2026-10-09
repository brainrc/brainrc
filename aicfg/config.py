"""Configuration: repo and render paths, TOML layering, harnesses, shared constants."""
from __future__ import annotations

import operator
import os
import re
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11; say so instead of a traceback
    sys.exit(f"aicfg needs Python 3.11+ (this is {sys.version.split()[0]}).")

from pathlib import Path


def find_core(pkg: Path) -> Path:
    """Core's content: bundled as aicfg/_core when aicfg is installed (pipx, uv), else the checkout."""
    bundled = pkg / "_core"
    return bundled if bundled.is_dir() else pkg.parent


REPO = find_core(Path(__file__).resolve().parent)


ROLES_LINK = Path("skills/spec-agent/roles")  # a symlink to ../../agents; a wheel holds copies


def installed() -> bool:
    """True when running from an installed package, whose files must never be written."""
    return REPO.name == "_core"


def command(sub: str) -> str:
    """How to run an aicfg command here, for hints: the installed `aicfg`, or the checkout's script."""
    return f"aicfg {sub}" if installed() else f"python3 scripts/aicfg.py {sub}"


def local_dir() -> Path:
    """Where machine-local files live (*.local.toml, rules/*.local.md): the checkout, or
    $AICFG_HOME when installed."""
    return aicfg_home() if installed() else REPO


# Hook commands under a hooks dir named ai-config or ai-config-<pack> are owned by ai-config
# and replaced on merge (so a disabled pack's hooks are removed too).
OWNED_HOOK = re.compile(r"/hooks/ai-config(?:-[a-z0-9-]+)?/")


OWNED_HOOK_MARKER = "/hooks/ai-config/"  # kept for callers that check a plain substring


# Placeholder in settings fragments, replaced with the source's hooks dir.
HOOKS_DIR_PLACEHOLDER = "{{hooks_dir}}"


BACKUPS_KEPT = 5


KNOWN_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash",
    "WebFetch", "WebSearch", "NotebookEdit", "TodoWrite",
    "AskUserQuestion", "Skill", "Agent", "TaskCreate", "TaskUpdate", "TaskList",
}


KNOWN_MODELS = {"haiku", "sonnet", "opus", "inherit"}


SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


EXTENSION_KEYS = {"domains", "intake_context", "ticket", "deliver_checks"}


KINDS = ("skills", "agents", "commands")


REQUIRED_CONNECTOR_OPS = ("fetch", "comment", "transition", "link_pr")  # references/connectors.md


H2 = re.compile(r"^## +(.+)$", re.M)


CORE_VERSION = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)$")


CONSTRAINT_CLAUSE = re.compile(r"^(>=|<=|==|!=|>|<)? *([0-9]+(?:\.[0-9]+){0,2})$")


CONSTRAINT_SYNTAX = 'comma-separated clauses of >=, >, <=, <, ==, != and a version, e.g. ">=0.1, <0.2"'


CHANGELOG_VERSION = re.compile(r"^## ([0-9]+\.[0-9]+\.[0-9]+)\b", re.M)


CHANGELOG_UNRELEASED = re.compile(r"^## +unreleased\b", re.M | re.I)


COMPARE = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt,
           "==": operator.eq, "!=": operator.ne}


class ConfigError(Exception):
    pass


def _read_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text()) if path.is_file() else {}


def _layered(name: str) -> dict[str, dict]:
    """<name>.toml with <name>.local.toml merged over it, one table at a time."""
    config = _read_toml(REPO / f"{name}.toml")
    for key, overrides in _read_toml(local_dir() / f"{name}.local.toml").items():
        config.setdefault(key, {}).update(overrides)
    return config


def load_harnesses(include_disabled: bool = False) -> dict[str, dict]:
    config = _layered("harnesses")
    return {n: h for n, h in config.items() if include_disabled or h.get("enabled", True)}


def expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path)))


def tilde(path: Path) -> str:
    return str(path).replace(str(Path.home()), "~", 1)


def aicfg_home() -> Path:
    """Where apply renders rules and extensions: outside any checkout, so packaged installs can
    read them too. $AICFG_HOME, else ~/.config/ai-config."""
    if os.environ.get("AICFG_HOME"):
        return expand(os.environ["AICFG_HOME"])
    return Path.home() / ".config" / "ai-config"


def legacy_instructions() -> Path:
    """Where rules were rendered before 0.3.16; apply removes it and re-points links."""
    return REPO / "dist" / "instructions.md"


def rendered_instructions() -> Path:
    return aicfg_home() / "instructions.md"


def rendered_agents_dir() -> Path:
    return aicfg_home() / "opencode" / "agents"


def home_extensions_file() -> Path:
    return aicfg_home() / "extensions.md"


def extensions_file() -> Path:
    """Deprecated in-repo copy of the rendered extensions, still written for packs that read it."""
    return REPO / "skills" / "spec-agent" / "references" / "extensions.md"


def hook_command_dir(hooks_dir: str) -> str:
    """hooks_dir as written into hook commands: `~` becomes `$HOME` so the shell expands it."""
    return "$HOME" + hooks_dir[1:] if hooks_dir.startswith("~") else hooks_dir


def pack_hooks_dir(hooks_dir: str, pack: str) -> str:
    """Packs get a sibling of the core hooks dir, never a subdir (that's a symlink into core)."""
    return hooks_dir.rstrip("/") + f"-{pack}"
