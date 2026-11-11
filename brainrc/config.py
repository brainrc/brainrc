"""Configuration: repo and render paths, TOML layering, harnesses, shared constants."""
from __future__ import annotations

import contextlib
import operator
import os
import re
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11; say so instead of a traceback
    sys.exit(f"brainrc needs Python 3.11+ (this is {sys.version.split()[0]}).")

from pathlib import Path


def find_core(pkg: Path) -> Path:
    """Core's content: bundled as brainrc/_core when brainrc is installed (pipx, uv), else the checkout."""
    bundled = pkg / "_core"
    return bundled if bundled.is_dir() else pkg.parent


REPO = find_core(Path(__file__).resolve().parent)


ROLES_LINK = Path("skills/spec-agent/roles")  # a symlink to ../../agents; a wheel holds copies


def installed() -> bool:
    """True when running from an installed package, whose files must never be written."""
    return REPO.name == "_core"


def command(sub: str) -> str:
    """How to run a brainrc command here, for hints: the installed `brainrc`, or the checkout's script."""
    return f"brainrc {sub}" if installed() else f"python3 scripts/brainrc.py {sub}"


def local_dir() -> Path:
    """Where machine-local files live (*.local.toml, rules/*.local.md): the checkout, or
    the settings home when installed."""
    return settings_home() if installed() else REPO


# Hook commands under a hooks dir named brainrc[-<pack>] (or the former ai-config[-<pack>])
# are owned by brainrc and replaced on merge (so a disabled pack's hooks are removed too).
OWNED_HOOK = re.compile(r"/hooks/(?:ai-config|brainrc)(?:-[a-z0-9-]+)?/")


OWNED_HOOK_MARKER = "/hooks/brainrc/"  # kept for callers that check a plain substring


# Placeholder in settings fragments, replaced with the source's hooks dir.
HOOKS_DIR_PLACEHOLDER = "{{hooks_dir}}"


BACKUPS_KEPT = 5


KNOWN_TOOLS = {
    "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash",
    "WebFetch", "WebSearch", "NotebookEdit", "TodoWrite",
    "AskUserQuestion", "Skill", "Agent", "Task", "TaskCreate", "TaskUpdate", "TaskList",
}


KNOWN_MODELS = {"haiku", "sonnet", "opus", "inherit"}


MODEL_ID = re.compile(r"^claude-[a-z0-9][a-z0-9.-]*$")  # a full model ID, e.g. claude-sonnet-5-5


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


PATH_KEYS = ("home", "skills", "agents", "agents_format", "commands", "plugin", "instructions",
             "hooks_dir", "settings", "mcp")


# Known keys of each table in <name>.toml / <name>.local.toml, and the type each must have.
LAYERED_KEYS = {
    "harnesses": {"enabled": bool, **dict.fromkeys(PATH_KEYS, str)},
    "packs": {"enabled": bool, "path": str, "git": str, "ref": str},
}


TOML_POSITION = re.compile(r" \(at (?:line (\d+), column \d+|end of document)\)$")


TABLE_HEADER = re.compile(r"^\s*\[\s*([^\]\s]+)\s*\]")


def toml_error(path: Path, text: str, e: tomllib.TOMLDecodeError) -> ConfigError:
    """`<file>:<line>: invalid TOML: <what>`; at end of document, the line is the last one."""
    m = TOML_POSITION.search(str(e))
    line = int(m[1]) if m and m[1] else max(len(text.splitlines()), 1)
    return ConfigError(f"{tilde(path)}:{line}: invalid TOML: {TOML_POSITION.sub('', str(e))}")


def line_of(text: str, table: str, key: str | None = None) -> int:
    """The line of `key =` inside [table] (top-level `table =` when key is None). tomllib keeps
    no positions, so scan: fall back to the [table] header, then `table =`, then line 1."""
    current, header, inline = None, None, None
    for n, line in enumerate(text.splitlines(), 1):
        if m := TABLE_HEADER.match(line):
            current = m[1].strip('"\'')
            header = header or (n if current == table else None)
        elif current == table and key and re.match(rf"\s*[\"']?{re.escape(key)}[\"']?\s*=", line):
            return n
        elif current is None and re.match(rf"\s*[\"']?{re.escape(table)}[\"']?\s*=", line):
            inline = n
    return (header if key else None) or inline or header or 1


def _read_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    text = path.read_text()
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise toml_error(path, text, e) from None


def _check_toml(name: str, path: Path, data: dict, known_tables: set[str] | None = None) -> list[str]:
    """Raise ConfigError, with file and line, for a value that isn't a table or a known key of
    the wrong type. Return warnings for unknown keys, and for tables outside known_tables."""
    text = path.read_text() if data else ""
    warnings = []
    for table, values in data.items():
        if not isinstance(values, dict):
            raise ConfigError(f"{tilde(path)}:{line_of(text, table)}: `{table}` must be a table, e.g. [{table}]")
        if known_tables is not None and table not in known_tables:
            warnings.append(f"{tilde(path)}:{line_of(text, table)}: unknown {name[:-2]} [{table}]")
        for key, value in values.items():
            kind = LAYERED_KEYS[name].get(key)
            if kind is None:
                warnings.append(f"{tilde(path)}:{line_of(text, table, key)}: unknown key `{key}` in [{table}]")
            elif not isinstance(value, kind):
                want = "true or false" if kind is bool else "a string"
                raise ConfigError(f"{tilde(path)}:{line_of(text, table, key)}: [{table}] `{key}` must be {want}")
    return warnings


def _layered(name: str, warnings: list[str] | None = None) -> dict[str, dict]:
    """<name>.toml with <name>.local.toml merged over it, one table at a time. Each file is
    checked before the merge, so an error names the file the bad value is in; warnings are
    added to `warnings` when given. A harness defined only in the local file still loads."""
    config: dict[str, dict] = {}
    for path in (REPO / f"{name}.toml", local_dir() / f"{name}.local.toml"):
        data = _read_toml(path)
        known = set(config) if name == "harnesses" and config else None
        found = _check_toml(name, path, data, known)
        if warnings is not None:
            warnings += found
        for key, overrides in data.items():
            config.setdefault(key, {}).update(overrides)
    return config


def check_config() -> list[str]:
    """Check harness and pack config up front, so a command stops on the first bad value before
    it does anything. Raises ConfigError; returns the warnings (unknown keys and harnesses)."""
    warnings: list[str] = []
    for name in LAYERED_KEYS:
        _layered(name, warnings)
    return warnings


def load_harnesses(include_disabled: bool = False, include_missing: bool = False,
                   defaults: bool = False) -> dict[str, dict]:
    """Harnesses from harnesses.toml with the local file over it. By default only the ones brainrc
    manages: enabled, and installed (or enabled in harnesses.local.toml, which forces it).
    include_missing keeps enabled ones that aren't installed; include_disabled keeps every one.
    defaults: each `${VAR:-default}` path as its default, whatever the environment says."""
    config = {n: {k: env_default(v, defaults) if k in PATH_KEYS and isinstance(v, str) else v
                  for k, v in h.items()} for n, h in _layered("harnesses").items()}
    if include_disabled:
        return config
    enabled = {n: h for n, h in config.items() if h.get("enabled", True)}
    if include_missing:
        return enabled
    forced = _forced()
    return {n: h for n, h in enabled.items() if n in forced or harness_installed(h)}


def harness_home(h: dict) -> Path | None:
    """The directory whose existence means the harness is installed: `home`, else the parent of its
    `instructions` or `skills` path (e.g. ~/.claude), else None."""
    if "home" in h:
        return expand(h["home"])
    key = next((k for k in ("instructions", "skills") if k in h), None)
    return expand(h[key]).parent if key else None


def harness_installed(h: dict) -> bool:
    home = harness_home(h)
    return home is None or home.is_dir()


def _forced() -> set[str]:
    """Harnesses managed even when not detected: those harnesses.local.toml enables explicitly,
    and those it defines that the shipped harnesses.toml doesn't (the user's own harness)."""
    shipped = _read_toml(REPO / "harnesses.toml")
    local = _read_toml(local_dir() / "harnesses.local.toml")
    return {n for n, t in local.items() if isinstance(t, dict)
            and (t.get("enabled") is True or (n not in shipped and t.get("enabled", True)))}


def missing_harnesses() -> dict[str, Path]:
    """Enabled harnesses that brainrc skips because they aren't installed, with the home it looked for."""
    managed = load_harnesses()
    return {n: harness_home(h) for n, h in load_harnesses(include_missing=True).items()
            if n not in managed and harness_home(h) is not None}


_SCOPE: frozenset[str] | None = None  # set by `status/apply --only`; None means every harness


def harness_scope() -> frozenset[str] | None:
    """The harnesses `--only` limits this run to, or None for all of them."""
    return _SCOPE


def in_scope(name: str) -> bool:
    return _SCOPE is None or name in _SCOPE


@contextlib.contextmanager
def only_harnesses(names: list[str] | None):
    """Limit what plan() and mcp_plan() touch to `names` (None: no limit) while the block runs.
    Harnesses outside the scope are left exactly as they are: no links, prunes or merges."""
    global _SCOPE
    old, _SCOPE = _SCOPE, frozenset(names) if names else None
    try:
        yield
    finally:
        _SCOPE = old


def check_only(names: list[str]) -> str | None:
    """Why `--only names` can't run (a name that isn't an enabled, installed harness), or None.
    Raises ConfigError for a broken harnesses.toml, as every command that reads it does."""
    every, enabled, missing = load_harnesses(include_disabled=True), load_harnesses(), missing_harnesses()
    for name in names:
        if name not in every:
            return f"--only {name}: no such harness (known: {', '.join(every)})"
        if name in missing:
            return (f"--only {name}: {tilde(missing[name])} doesn't exist, so {name} isn't installed "
                    f"(set `[{name}] enabled = true` in harnesses.local.toml to manage it anyway)")
        if name not in enabled:
            return (f"--only {name}: {name} is disabled (`enabled = false` in harnesses.toml "
                    "or harnesses.local.toml)")
    return None


def expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path)))


def tilde(path: Path) -> str:
    return str(path).replace(str(Path.home()), "~", 1)


HARNESS_VARS = ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "XDG_CONFIG_HOME")  # read by harnesses.toml (#110)


ENV_DEFAULT = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*):-([^}]*)\}")


def env_dir(var: str, default: str) -> str:
    """$var when it holds an absolute path (after ~), else default; a path under ~ is written with ~,
    so hook commands and the manifest stay portable. Unset, empty or relative: default (XDG's rule)."""
    value = os.path.expanduser(os.environ.get(var, ""))
    if not value or not os.path.isabs(value):
        return default
    value, home = os.path.normpath(value), str(Path.home())
    if value == home or value.startswith(home.rstrip("/") + "/"):
        return "~" + value[len(home.rstrip("/")):]
    return value


def env_default(path: str, defaults: bool = False) -> str:
    """A harnesses.toml path with each `${VAR:-default}` resolved by env_dir (to its default when
    `defaults`)."""
    return ENV_DEFAULT.sub(lambda m: m[2] if defaults else env_dir(m[1], m[2]), path)


def harness_vars(name: str) -> list[str]:
    """The env vars that name's harnesses.toml paths read, e.g. ["CLAUDE_CONFIG_DIR"]."""
    try:
        h = _layered("harnesses").get(name, {})
    except ConfigError:
        return []
    return sorted({m[1] for k, v in h.items() if k in PATH_KEYS and isinstance(v, str)
                   for m in ENV_DEFAULT.finditer(v)})


def ignored_vars() -> list[str]:
    """The harness env vars that are set but not to an absolute path, so brainrc uses the default."""
    return [v for v in HARNESS_VARS
            if os.environ.get(v) and not os.path.isabs(os.path.expanduser(os.environ[v]))]


def claude_json() -> Path:
    """Claude Code's MCP file: .claude.json inside $CLAUDE_CONFIG_DIR, else ~/.claude.json."""
    return expand(env_dir("CLAUDE_CONFIG_DIR", "~") + "/.claude.json")


def claude_dir() -> Path:
    """Claude Code's config dir: $CLAUDE_CONFIG_DIR, else ~/.claude."""
    return expand(env_dir("CLAUDE_CONFIG_DIR", "~/.claude"))


def _xdg_home() -> Path | None:
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    return Path(xdg) / "brainrc" if xdg and os.path.isabs(xdg) else None


def new_home() -> Path:
    """The settings home: BRAINRC_HOME, XDG, ~/.config/brainrc."""
    if os.environ.get("BRAINRC_HOME"):
        return expand(os.environ["BRAINRC_HOME"])
    return _xdg_home() or Path.home() / ".config" / "brainrc"


def _legacy_home() -> Path:
    return Path.home() / ".config" / "ai-config"


def unmigrated_home() -> tuple[str, Path] | None:
    """The old home that still holds the user's settings and is no longer read, as ("env", dir)
    for AICFG_HOME or ("legacy", dir) for ~/.config/ai-config; None when nothing needs migrating."""
    if os.environ.get("BRAINRC_HOME"):  # an explicit new home: the old ones are just unused
        return None
    new = new_home()
    if os.environ.get("AICFG_HOME") and (not new.is_dir() or not any(new.iterdir())):
        return "env", expand(os.environ["AICFG_HOME"])
    if not new.exists() and _legacy_home().exists():
        return "legacy", _legacy_home()
    return None


def former_homes() -> list[Path]:
    """Old homes (AICFG_HOME, ~/.config/ai-config) that are not the resolved home."""
    home = settings_home()
    olds = [expand(os.environ["AICFG_HOME"])] if os.environ.get("AICFG_HOME") else []
    olds.append(_legacy_home())
    return [d for i, d in enumerate(olds) if not _same_dir(d, home) and d not in olds[:i]]


def _same_dir(a: Path, b: Path) -> bool:
    """Equal paths, or two existing paths to one directory (a home reached through a symlink)."""
    return a == b or (a.exists() and b.exists() and os.path.samefile(a, b))


def settings_home() -> Path:
    """Where apply renders rules and extensions: outside any checkout, so packaged installs can
    read them too. $BRAINRC_HOME, $XDG_CONFIG_HOME/brainrc (absolute only), or ~/.config/brainrc."""
    return new_home()


def legacy_instructions() -> Path:
    """Where rules were rendered before 0.3.16; apply removes it and re-points links."""
    return REPO / "dist" / "instructions.md"


def rendered_instructions() -> Path:
    return settings_home() / "instructions.md"


def rendered_agents_dir() -> Path:
    return settings_home() / "opencode" / "agents"


def home_extensions_file() -> Path:
    return settings_home() / "extensions.md"


def extensions_file() -> Path:
    """Deprecated in-repo copy of the rendered extensions, still written for packs that read it."""
    return REPO / "skills" / "spec-agent" / "references" / "extensions.md"


def hooks_copy_root() -> Path:
    """Where an installed brainrc copies core's hooks, so they outlive a versioned package path."""
    return settings_home() / "hooks" / "core"


def hook_command_dir(hooks_dir: str) -> str:
    """hooks_dir as written into hook commands: `~` becomes `$HOME` so the shell expands it."""
    return "$HOME" + hooks_dir[1:] if hooks_dir.startswith("~") else hooks_dir


def pack_hooks_dir(hooks_dir: str, pack: str) -> str:
    """Packs get a sibling of the core hooks dir, never a subdir (that's a symlink into core)."""
    return hooks_dir.rstrip("/") + f"-{pack}"


def former_hooks_dirs(hooks_dir: str) -> list[str]:
    """The pre-rename sibling of a hooks dir named brainrc; a dir the user named is used as given."""
    d = hooks_dir.rstrip("/")
    return [d[:-len("brainrc")] + "ai-config"] if d.endswith("/brainrc") else []


def former_plugin_paths(plugin: str) -> list[str]:
    """The pre-rename link for a plugin named brainrc-guard.js; a plugin the user named is used as given."""
    head, _, name = plugin.rpartition("/")
    return [f"{head}/ai-config-guard.js"] if name == "brainrc-guard.js" else []
