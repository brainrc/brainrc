"""Hook commands that run natively on Windows (#178).

The settings fragments spell each hook as a POSIX shell line: `f="<dir>/guard.py"; [ ! -f "$f" ] ||
python3 "$f"` (pass when the guard is gone) or `... else echo '<allow JSON>'; fi`. macOS and Linux
keep exactly that. On Windows a tool runs its hook command through PowerShell, cmd or Git Bash,
and Python is `py -3` (or `python`), not `python3`, so apply writes each of brainrc's hooks as one
Python call that does the same thing without any shell syntax:

    py -3 -X utf8 -I -c "import os,runpy,sys;f='C:/Users/acme/.codex/hooks/brainrc/guard.py';..."

The line holds no character any of those shells reads inside double quotes ($ ` % ! ^ & | < >),
so it means the same in each. Each adapter says where the line goes (adapters/base.py
`windows_hook`): Claude Code takes it as an exec-form hook with no shell at all, Codex as its
`commandWindows`, Copilot as its `powershell`, and the rest in place of `command`.
"""
from __future__ import annotations

import functools
import json
import os
import re
import shutil
import subprocess
import sys

from .config import ConfigError

# The forms core's fragments use; packs that write `python3 "<path>"` get the plain one.
_PATH = r'f="(?P<path>[^"]+\.py)"; '
FORMS = (
    re.compile(_PATH + r'\[ ! -f "\$f" \] \|\| (?:! command -v python3 >/dev/null \|\| )?python3 "\$f"'),
    re.compile(_PATH + r"if \[ -f \"\$f\" \]; then python3 \"\$f\"; else echo '(?P<fallback>\{.*\})'; fi"),
    re.compile(r'python3 "(?P<path>[^"]+\.py)"'),  # runs whether or not the file is there, as it did
)
# Characters that mean something to cmd, PowerShell or a POSIX shell inside double quotes, or to
# the Python string the path sits in.
UNSAFE = set("\"'$`%!^&|<>\n\r")


def windows_hooks() -> bool:
    """True when apply writes the Windows form (this machine is Windows)."""
    return os.name == "nt"


# Every Windows hook runs isolated (-I: no module from the project folder, which `-c` would put
# first on sys.path) and in UTF-8 (-X utf8: -I ignores PYTHONUTF8, and the ANSI code page can't
# read every payload, so a guard would fail open on a folder named `Łódź`).
FLAGS = ["-X", "utf8", "-I"]


def _usable(exe: str, args: list[str]) -> bool:
    """exe runs and is Python 3.11 or newer (the guards need it); not the Microsoft Store stub."""
    if "\\windowsapps\\" in os.path.normcase(exe).replace("/", "\\"):
        return False
    try:
        return subprocess.run([exe, *args, "-c", "import sys;sys.exit(sys.version_info<(3,11))"],
                              capture_output=True, timeout=15).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@functools.lru_cache(maxsize=None)
def python() -> tuple[str, list[str]]:
    """The Python a Windows hook runs, as a full path: the `py` launcher (`py -3`), then `python`
    on PATH, each only if it is 3.11 or newer, then the interpreter brainrc runs under."""
    for name, args in (("py", ["-3"]), ("python", [])):
        found = shutil.which(name)
        if found and _usable(found, args):
            return found, args
    return sys.executable, []


def parse(command: str) -> tuple[str, dict | None, bool] | None:
    """(guard path, JSON to print when it is gone, run only if present) for a command in one of
    FORMS, else None (a pack's own command is left as it is)."""
    for form in FORMS:
        m = form.fullmatch(command.strip())
        if m:
            fallback = m.groupdict().get("fallback")
            return m["path"], json.loads(fallback) if fallback else None, form is not FORMS[-1]
    return None


def windows(hooks: dict, adapter) -> dict:
    """hooks (Claude Code's shape: event -> groups, each with `hooks`, or flat entries) with each
    of brainrc's commands in its Windows form, written where adapter puts it."""
    exe, args = python()
    args = [*args, *FLAGS]
    out = {}
    for event, groups in hooks.items():
        out[event] = []
        for group in groups:
            if isinstance(group.get("hooks"), list):
                group = group | {"hooks": [_one(h, adapter, exe, args) for h in group["hooks"]]}
            else:
                group = _one(group, adapter, exe, args)
            out[event].append(group)
    return out


def _one(hook: dict, adapter, exe: str, args: list[str]) -> dict:
    parsed = parse(str(hook.get("command", ""))) if isinstance(hook, dict) else None
    if parsed is None:
        return hook
    path, fallback, only_if_present = parsed
    return adapter.windows_hook(hook, exe, args, code(native_path(path), fallback, only_if_present))


def expand(path: str) -> str:
    """path with `$HOME` and `~` expanded (cmd and PowerShell don't set HOME) and `/` separators."""
    home = os.path.expanduser("~")
    if path.startswith("$HOME"):
        path = home + path[len("$HOME"):]
    return os.path.expanduser(path).replace("\\", "/")


def runs(hook: dict) -> str:
    """The text of what a hook entry runs on this machine: the Windows field when apply wrote one
    (Codex's `commandWindows`, Copilot's `powershell`, Claude Code's exec-form code), else `command`."""
    if windows_hooks():
        for key in ("commandWindows", "powershell"):
            if isinstance(hook.get(key), str):
                return hook[key]
        if isinstance(hook.get("args"), list) and hook["args"]:
            return str(hook["args"][-1])
    return str(hook.get("command") or "")


def native_path(path: str) -> str:
    """The guard's path as the hook gives it: `~/...` under the home directory, as the POSIX line's
    `$HOME` keeps it (one lock, the same file on every machine), else absolute (expand). Refused
    if a shell would read it."""
    path = expand(path)
    home = os.path.expanduser("~").replace("\\", "/").rstrip("/")
    if os.path.normcase(path).startswith(os.path.normcase(home + "/")):
        path = "~" + path[len(home):]
    bad = sorted(UNSAFE & set(path))
    if bad:
        raise ConfigError(f"hook path {path!r} holds {' '.join(bad)}, which a Windows hook command can't "
                          "carry; set the tool's hooks_dir in harnesses.local.toml to a path without them")
    return path


def code(path: str, fallback: dict | None, only_if_present: bool) -> str:
    """The Python that runs the guard at path as its own script (so it finds the guards beside
    it): when it is gone, nothing (or the fallback JSON) and exit 0, as the POSIX line does."""
    # As `python3 <file>` would: the file's folder first on sys.path, then the file as __main__.
    # A `~/` path is expanded when the hook runs (Python reads USERPROFILE on Windows).
    path = f"os.path.expanduser('{path}')" if path.startswith("~") else f"'{path}'"
    run = "sys.path.insert(0,os.path.dirname(f)),runpy.run_path(f,run_name='__main__')"
    if not only_if_present:
        return f"import os,runpy,sys;f={path};({run})"
    if fallback is None:
        return f"import os,runpy,sys;f={path};os.path.isfile(f) and ({run})"
    if not all(isinstance(k, str) and k.isidentifier() and isinstance(v, str) and not UNSAFE & set(v)
               for k, v in fallback.items()):
        raise ConfigError(f"a hook's fallback output {fallback!r} can't be written as a Windows hook command")
    out = ",".join(f"{k}={v!r}" for k, v in fallback.items())
    return f"import json,os,runpy,sys;f={path};({run}) if os.path.isfile(f) else print(json.dumps(dict({out})))"


def line(exe: str, args: list[str], source: str, shell: str | None) -> str:
    """One command line for shell ("powershell", "cmd", or None when the tool doesn't say)."""
    found = shutil.which("py")
    if os.path.splitext(os.path.basename(exe))[0].lower() == "py" and found and \
            os.path.normcase(found) == os.path.normcase(exe):
        program = "py"  # the launcher: on PATH wherever Windows has it, and the same in every shell
    else:
        program = exe.replace("\\", "/")
        bad = sorted((UNSAFE - {'"'}) & set(program))
        if bad:
            raise ConfigError(f"the Python hooks would run, {program!r}, holds {' '.join(bad)}, which a "
                              "Windows hook command can't carry; install the py launcher")
        if " " in program:
            if shell is None:  # no one quoting reads the same in cmd, PowerShell and Git Bash
                raise ConfigError(f"the Python hooks would run, {program!r}, has a space in its path and "
                                  "this tool doesn't say which shell runs its hooks; install the py launcher "
                                  "or a Python whose path has no spaces")
            program = f'& "{program}"' if shell == "powershell" else f'call "{program}"'
    return " ".join([program, *args, "-c", f'"{source}"'])
