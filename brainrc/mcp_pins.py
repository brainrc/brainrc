"""MCP tool pins (#290): `brainrc pin-mcp` starts each stdio server brainrc installs for Claude
Code, lists its tools, shows what changed against $BRAINRC_HOME/mcp-pins.json, and records the
hash of each tool definition once you approve. A SessionStart hook in Claude Code
(overrides/claude/hooks/check_mcp_pins.py) warns when a pinned server's tools change after that.

HTTP servers aren't pinned: brainrc has no network code. `apply` names each installed stdio
server that isn't pinned, or whose command changed since, without starting anything.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from . import config
from .config import ConfigError, settings_home, tilde
from .mcp import check_servers, mcp_plan
from .packs import printable
from .sources import sources

HOOK = Path("overrides") / "claude" / "hooks" / "check_mcp_pins.py"
TIMEOUT = 60.0  # a first `npx -y` may download the server
SPEC = ("command", "args", "env_from")


def client():
    """The hook module: one MCP client and one tool hash for the hook and this command."""
    spec = importlib.util.spec_from_file_location("brainrc_check_mcp_pins", config.REPO / HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pins_path() -> Path:
    return settings_home() / "mcp-pins.json"


def read() -> dict[str, dict]:
    try:
        data = json.loads(pins_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    servers = data.get("servers") if isinstance(data, dict) else None
    return servers if isinstance(servers, dict) else {}


def write(servers: dict[str, dict]) -> None:
    path = pins_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps({"version": 1, "servers": dict(sorted(servers.items()))}, indent=2,
                              sort_keys=True) + "\n")
    tmp.replace(path)


def spec(server: dict) -> dict:
    """What the pin records of the server's definition: how to start it, never a value."""
    return {k: server.get(k, []) for k in SPEC if k == "command" or server.get(k)}


def installed() -> dict[str, dict]:
    """The servers apply installs for Claude Code on this machine (none unless the profile is full)."""
    srcs = sources()
    errors = check_servers(srcs)
    if errors:
        raise ConfigError(errors[0])
    return {n: s for sync in mcp_plan(srcs) if sync.harness == "claude" for n, s in sync.servers.items()}


def unpinned(servers: dict[str, dict]) -> list[str]:
    """For apply, without starting anything: each stdio server with no pin, or a different one."""
    pins, notes = read(), []
    for name, s in sorted(servers.items()):
        if "command" not in s:
            continue
        pin = pins.get(name)
        if not isinstance(pin, dict):
            notes.append(f"{name}: its tools aren't pinned yet")
        elif {k: pin[k] for k in SPEC if k in pin} != spec(s):
            notes.append(f"{name}: its command changed since its tools were pinned")
    return notes


def report_unpinned(servers: dict[str, dict]) -> None:
    for note in unpinned(servers):
        print(f"{'MCP-PIN':9} {note}; `{config.command('pin-mcp')}` approves them")


def _shown(s: dict) -> str:
    return printable(" ".join([str(s.get("command", "?")), *map(str, s.get("args", []))]))


def prune(servers: dict[str, dict]) -> None:
    """apply: drop the pins of servers it no longer installs, so the hook stops starting them."""
    pins = read()
    gone = sorted(set(pins) - {n for n, s in servers.items() if "command" in s})
    if gone:
        write({n: p for n, p in pins.items() if n not in gone})
        for name in gone:
            print(f"{'UNPIN':9} {name}: no longer installed")


def _confirm(added: int, yes: bool) -> bool:
    from .permissions import interactive
    if yes:
        return True
    if not interactive():
        print(f"\nNothing written. {added} tool definition(s) to approve (PIN + and ~ above), and there "
              "is no terminal to ask in. Re-run with --yes to approve them.")
        return False
    try:
        answer = input(f"\nApprove {added} tool definition(s) (PIN + and ~ above)? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() in ("y", "yes"):
        return True
    print("Nothing written.")
    return False


def cmd_pin_mcp(names: list[str], yes: bool = False) -> int:
    try:
        servers = installed()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    unknown = sorted(set(names) - set(servers))
    if unknown:
        listed = ", ".join(sorted(servers)) or "none"
        print(f"ERROR {', '.join(unknown)}: not an MCP server brainrc installs for Claude Code here "
              f"(servers: {listed})")
        return 2
    pins, mcp, failed = read(), client(), False
    if not servers and not pins:
        need = "" if config.installs("mcp") else " (MCP servers need profile = \"full\")"
        print(f"No MCP servers to pin: brainrc installs none for Claude Code on this machine{need}.")
        return 0
    new, approve = dict(pins), 0
    for name, s in sorted(servers.items()):
        if names and name not in names:
            continue
        if "command" not in s:
            print(f"{'SKIP':9} {name}: an HTTP server; brainrc has no network code, so it pins stdio servers only")
            continue
        try:
            tools = mcp.list_tools(s["command"], s.get("args", []), TIMEOUT)
        except (OSError, TimeoutError, ValueError) as e:
            print(f"ERROR {name}: couldn't list its tools ({e}); its pin is left as it was")
            failed = True
            continue
        hashes = {t["name"]: mcp.tool_hash(t) for t in tools}
        old = pins.get(name) if isinstance(pins.get(name), dict) else {}
        was = old.get("tools", {})
        lines = [("+", n, "") for n in sorted(set(hashes) - set(was))]
        lines += [("~", n, "  (definition changed)") for n in sorted(set(hashes) & set(was)) if hashes[n] != was[n]]
        lines += [("-", n, "") for n in sorted(set(was) - set(hashes))]
        for sign, n, why in sorted(lines, key=lambda x: x[1]):
            print(f"{'PIN':9} {name:9} {sign} tool   {printable(n)}{why}")
        before = {k: old[k] for k in SPEC if k in old}
        if old and before != spec(s):  # the same tools from another command is still a new approval
            print(f"{'PIN':9} {name:9} ~ command {_shown(before)} -> {_shown(spec(s))}")
            approve += 1
        elif not lines:
            print(f"{'CURRENT':9} {name}: {len(hashes)} tool(s), unchanged")
        approve += sum(sign != "-" for sign, _, _ in lines)
        new[name] = {**spec(s), "tools": hashes}
    for gone in sorted(set(new) - set(servers)):
        print(f"{'UNPIN':9} {gone}: no longer installed")
        del new[gone]
    if new == pins:
        return 1 if failed else 0
    if approve and not _confirm(approve, yes):
        return 1
    write(new)
    print(f"\nPinned in {tilde(pins_path())}. Claude Code warns at session start when one of these changes.")
    return 1 if failed else 0
