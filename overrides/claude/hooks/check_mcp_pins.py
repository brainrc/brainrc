#!/usr/bin/env python3
"""Claude Code SessionStart hook: warn when an MCP server's tools changed after you approved them.

`brainrc pin-mcp` records a hash of each tool definition (name, description, input schema, ...)
of the stdio servers brainrc installs, in $BRAINRC_HOME/mcp-pins.json. At session start this
hook starts each pinned server, lists its tools over MCP's stdio JSON-RPC, and warns, in the
session and to the model, about every tool that was changed, added or removed since (#290).

Fail-open and bounded: a missing or unreadable pin file, a server that won't start, or one that
doesn't answer within BUDGET seconds warns nothing and blocks nothing. It has no network code;
it only runs the servers' own commands. Each run writes its duration and per-server outcome to
mcp-pins.last.json beside the pins, so the hook's latency can be measured.

`brainrc pin-mcp` imports this file for list_tools and tool_hash, so both use one client.
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

BUDGET = 4.0  # seconds for every server together; the fragment gives the hook 10
MISSES = 3  # sessions in a row a server went unchecked before the hook says so
SHOWN = 10  # tool names shown per server; the rest are counted
SAFE_NAME = re.compile(r"[A-Za-z0-9_.-]{1,64}")
PROTOCOL = "2025-06-18"
PINS, LAST = "mcp-pins.json", "mcp-pins.last.json"


def settings_home() -> Path:
    """brainrc's settings home: $BRAINRC_HOME, $XDG_CONFIG_HOME/brainrc (absolute), ~/.config/brainrc."""
    if os.environ.get("BRAINRC_HOME"):
        return Path(os.path.expandvars(os.environ["BRAINRC_HOME"])).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    return Path(xdg) / "brainrc" if os.path.isabs(xdg) else Path.home() / ".config" / "brainrc"


def tool_hash(tool: dict) -> str:
    """The hash of one tool's definition: every field but `_meta`, as canonical JSON."""
    body = {k: v for k, v in tool.items() if k != "_meta"}
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stop(proc: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)  # npx and the like start children of their own
        else:
            proc.kill()
    except OSError:
        pass
    try:  # stdout is the reader thread's to close: closing it here can block on a helper's pipe
        proc.stdin.close()
    except OSError:
        pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass


def list_tools(command: str, args: list[str], timeout: float) -> list[dict]:
    """The server's tools, from initialize then every page of tools/list. Raises OSError,
    TimeoutError or ValueError; the server is stopped either way."""
    deadline = time.monotonic() + timeout
    proc = subprocess.Popen([command, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, start_new_session=os.name == "posix",
                            cwd=Path.home())  # the same for pin-mcp and the hook, whatever the project
    lines: queue.Queue = queue.Queue()

    def read() -> None:
        with proc.stdout:
            for line in proc.stdout:
                lines.put(line)
        lines.put(None)

    threading.Thread(target=read, daemon=True).start()

    def send(message: dict) -> None:
        proc.stdin.write((json.dumps({"jsonrpc": "2.0", **message}) + "\n").encode())
        proc.stdin.flush()

    def answer(id_: int) -> dict:
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError(f"no answer within {timeout:g}s")
            try:
                line = lines.get(timeout=left)
            except queue.Empty:
                raise TimeoutError(f"no answer within {timeout:g}s") from None
            if line is None:
                raise ValueError("the server exited")
            try:
                msg = json.loads(line)
            except ValueError:
                continue  # a server's stray log line on stdout
            if not isinstance(msg, dict) or msg.get("id") != id_ or "method" in msg:
                continue  # a notification, or a request from the server that happens to use our id
            if "error" in msg:
                err = msg["error"]
                raise ValueError(f"error from the server: {err.get('message', err) if isinstance(err, dict) else err}")
            result = msg.get("result")
            if not isinstance(result, dict):
                raise ValueError("a malformed answer from the server")
            return result

    try:
        send({"id": 1, "method": "initialize", "params": {
            "protocolVersion": PROTOCOL, "capabilities": {},
            "clientInfo": {"name": "brainrc-mcp-pins", "version": "1"}}})
        answer(1)
        send({"method": "notifications/initialized"})
        tools, cursor, id_ = [], None, 2
        while True:
            send({"id": id_, "method": "tools/list", "params": {"cursor": cursor} if cursor else {}})
            result = answer(id_)
            if not isinstance(result.get("tools", []), list):
                raise ValueError("a malformed tools list from the server")
            tools += [t for t in result.get("tools", []) if isinstance(t, dict) and isinstance(t.get("name"), str)]
            cursor, id_ = result.get("nextCursor"), id_ + 1
            if cursor is not None and not isinstance(cursor, str):
                raise ValueError("a malformed cursor from the server")
            if not cursor:
                return tools
    except (BrokenPipeError, ConnectionError) as e:
        raise ValueError("the server closed its input") from e
    finally:
        _stop(proc)


def compare(pinned: dict[str, str], tools: list[dict]) -> list[str]:
    """`changed X`, `added X`, `removed X` for each tool that differs from its pin."""
    now = {t["name"]: tool_hash(t) for t in tools}
    out = [f"changed {n}" for n in sorted(set(now) & set(pinned)) if now[n] != pinned[n]]
    out += [f"added {n}" for n in sorted(set(now) - set(pinned))]
    return out + [f"removed {n}" for n in sorted(set(pinned) - set(now))]


def check(servers: dict, budget: float) -> dict[str, list[str] | str]:
    """Each pinned server's changes (a list, empty when unchanged), or why it wasn't checked."""
    results: dict[str, list[str] | str] = {}

    def one(name: str, pin: dict) -> None:
        try:
            results[name] = compare(pin.get("tools", {}), list_tools(pin["command"], pin.get("args", []), budget))
        except TimeoutError:
            results[name] = "timeout"
        except Exception:  # fail open: anything else is "not checked", never a warning
            results[name] = "failed"

    threads = [threading.Thread(target=one, args=(n, p), daemon=True)
               for n, p in sorted(servers.items()) if isinstance(p, dict) and isinstance(p.get("command"), str)]
    for t in threads:
        t.start()
    end = time.monotonic() + budget + 1
    for t in threads:
        t.join(max(0.0, end - time.monotonic()))
    return {n: results.get(n, "timeout") for n in sorted(servers) if isinstance(servers[n], dict)}


def _shown(change: str) -> str:
    """`changed <name>` with a name the server chose: shown only if it is a plain identifier,
    since it lands in the model's context under brainrc's warning."""
    verb, _, name = change.partition(" ")
    return f"{verb} {name}" if SAFE_NAME.fullmatch(name) else f"{verb} a tool with an unusual name"


def message(results: dict, unchecked: list[str] | tuple = ()) -> dict | None:
    """The hook's output: a warning to the session and the model for changed tools, and a note
    to the session alone for servers that went unchecked MISSES sessions in a row."""
    changed = {n: r for n, r in results.items() if isinstance(r, list) and r}
    lines = []
    if changed:
        parts = []
        for n, r in changed.items():
            more = f", and {len(r) - SHOWN} more" if len(r) > SHOWN else ""
            parts.append(f"{n}: {', '.join(map(_shown, r[:SHOWN]))}{more}")
        what = "; ".join(parts)
        lines.append(f"brainrc: MCP tools changed since you approved them ({what}). Review and "
                     "re-approve with `brainrc pin-mcp`.")
    if unchecked:
        lines.append(f"brainrc couldn't check the tools of {', '.join(unchecked)} in the last {MISSES} "
                     f"sessions (no answer within {BUDGET:g}s, or it didn't start). `brainrc pin-mcp` "
                     "shows why.")
    if not lines:
        return None
    out: dict = {"systemMessage": " ".join(lines)}
    if changed:
        out["hookSpecificOutput"] = {"hookEventName": "SessionStart", "additionalContext": (
            f"brainrc warning: these MCP tools changed since the user approved them: {what}. Their "
            "definitions may now ask for something else. Don't call them until the user has "
            "reviewed them and run `brainrc pin-mcp`.")}
    return out


def main() -> int:
    start = time.monotonic()
    home = settings_home()
    try:
        data = json.loads((home / PINS).read_text(encoding="utf-8"))
        servers = data.get("servers") or {}
    except (OSError, ValueError, AttributeError):
        return 0  # nothing pinned on this machine
    if not isinstance(servers, dict) or not servers:
        return 0
    results = check(servers, BUDGET)
    try:
        before = json.loads((home / LAST).read_text(encoding="utf-8")).get("misses", {})
    except (OSError, ValueError, AttributeError):
        before = {}
    misses = {n: (before.get(n, 0) if isinstance(before.get(n), int) else 0) + 1
              for n, r in results.items() if isinstance(r, str)}
    out = message(results, sorted(n for n, k in misses.items() if k % MISSES == 0))
    if out:
        print(json.dumps(out))
    try:
        record = {"elapsed_ms": round((time.monotonic() - start) * 1000),
                  "servers": {n: r if isinstance(r, str) else ("changed" if r else "same") for n, r in results.items()},
                  "misses": misses}
        tmp = home / (LAST + ".tmp")
        tmp.write_text(json.dumps(record, indent=2) + "\n")
        tmp.replace(home / LAST)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # fail open
        sys.exit(0)
