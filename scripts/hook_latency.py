#!/usr/bin/env python3
"""Measure what core's hooks add to each tool call: median and p95 wall time (#299).

Each case runs the hooks a real tool call fires, the way the tool runs them: the hook command
from the settings fragment, through `sh -c`, one fresh `python3` per hook, the matching
PreToolUse hooks of one Claude Code call in parallel. SessionStart's MCP pin check runs once per
session, not per call, and is measured with no pins and with one pinned local stdio server.

    python3 scripts/hook_latency.py [--runs 50] [--json] [--summary FILE]

Stdlib only. It writes nothing outside a temporary $BRAINRC_HOME.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brainrc.plan import render_fragment  # noqa: E402  (the same rendering `apply` installs)

CLAUDE = ROOT / "overrides" / "claude"
CURSOR = ROOT / "overrides" / "cursor"
WARMUP = 3

# A tiny MCP server: answers initialize and tools/list over stdio, like the ones `pin-mcp` pins.
SERVER = r'''
import json, sys
for line in sys.stdin:
    msg = json.loads(line)
    if "id" not in msg:
        continue
    if msg["method"] == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "bench"}}
    else:
        result = {"tools": [{"name": "echo", "description": "Echo.", "inputSchema": {"type": "object"}}]}
    print(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": result}), flush=True)
'''

# (case, Claude Code tool name, tool input): typical calls, none of which a guard objects to.
CALLS = [
    ("Bash: git status", "Bash", {"command": "git status"}),
    ("Bash: pipeline", "Bash", {"command": "grep -rn TODO src | sort | head -20 && python3 -m unittest -q"}),
    ("Read", "Read", {"file_path": "src/app.py"}),
    ("Edit", "Edit", {"file_path": "src/app.py", "old_string": "x = 1", "new_string": "x = 2\n" * 200}),
    ("MCP tool", "mcp__github__get_issue", {"owner": "acme", "repo": "app", "issue_number": 1}),
]


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile: the smallest value with at least pct% of values at or below it."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * pct / 100) - 1)] if ordered else 0.0


def matches(matcher: str | None, tool: str) -> bool:
    """Claude Code's matcher: empty or `*` is every tool, anything else a regex on the whole name."""
    return not matcher or matcher == "*" or re.fullmatch(matcher, tool) is not None


def hook_commands(event: str, tool: str | None = None) -> list[str]:
    """Claude Code's fragment commands for event (and tool), rendered as `apply` renders them, with
    the hooks directory at the checkout's."""
    fragment = render_fragment(CLAUDE / "settings.fragment.json", str(CLAUDE / "hooks"))
    return [h["command"] for group in fragment["hooks"].get(event, [])
            if tool is None or matches(group.get("matcher"), tool) for h in group["hooks"]]


def cursor_commands(event: str) -> list[str]:
    fragment = render_fragment(CURSOR / "settings.fragment.json", str(CURSOR / "hooks"))
    return [h["command"] for h in fragment["hooks"].get(event, [])]


def run(command: str, payload: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["sh", "-c", command], input=payload, capture_output=True, text=True, env=env,
                          timeout=30, check=False)


def checked(command: str, payload: str, env: dict) -> None:
    """Run once untimed and fail loudly if the hook is missing, fails or objects: a skipped or
    broken hook would otherwise be timed as a fast success."""
    script = re.search(r'f="([^"]+)"', command)
    if script and not Path(script[1]).is_file():
        raise SystemExit(f"hook not found: {script[1]}")
    done = run(command, payload, env)
    if done.returncode != 0 or re.search(r'"(deny|ask)"', done.stdout):
        raise SystemExit(f"hook failed or objected ({done.returncode}): {command}\n{done.stdout}{done.stderr}")


def timed(fn, runs: int) -> list[float]:
    for _ in range(WARMUP):
        fn()
    out = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        out.append((time.perf_counter() - start) * 1000)
    return out


def parallel(commands: list[str], payload: str, env: dict):
    """One call of the tool: its hooks in parallel, as Claude Code runs them. The pool is made
    once, outside the timed calls."""
    for c in commands:
        checked(c, payload, env)
    if len(commands) <= 1:
        return lambda: [run(c, payload, env) for c in commands]
    pool = ThreadPoolExecutor(len(commands))
    return lambda: list(pool.map(lambda c: run(c, payload, env), commands))


def claude_call(tool: str, tool_input: dict, env: dict):
    commands = hook_commands("PreToolUse", tool)
    payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input,
                          "cwd": "/tmp/project", "session_id": "bench"})
    return parallel(commands, payload, env), len(commands)


def cursor_call(event: dict, env: dict):
    commands = cursor_commands(event["hook_event_name"])
    return parallel(commands, json.dumps(event), env), len(commands)


def cases(home: Path) -> list[tuple[str, str, int, object]]:
    env = {**os.environ, "BRAINRC_HOME": str(home)}
    # The floor any Python hook pays: a shell and an interpreter that does nothing.
    out = [("Baseline", "sh + python3 -c pass", 0, lambda: run("python3 -c pass", "", env))]
    for name, tool, tool_input in CALLS:
        fn, hooks = claude_call(tool, tool_input, env)
        out.append(("Claude Code", name, hooks, fn))
    # Cursor runs one hook per event; its guard.py runs the Claude guards the event needs.
    fn, _ = cursor_call({"hook_event_name": "beforeShellExecution", "command": "git status"}, env)
    out.append(("Cursor", "shell command", 2, fn))
    fn, _ = cursor_call({"hook_event_name": "beforeReadFile", "file_path": "src/app.py"}, env)
    out.append(("Cursor", "file read", 1, fn))
    start = hook_commands("SessionStart")
    out.append(("Claude Code", "session start, no MCP pins", len(start), parallel(start, "{}", env)))
    pinned = home.parent / "pinned"
    pinned.mkdir()
    (pinned / "server.py").write_text(SERVER)
    spec = importlib.util.spec_from_file_location("check_mcp_pins", CLAUDE / "hooks" / "check_mcp_pins.py")
    pins = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pins)  # pin the server with the hook's own client, as `pin-mcp` does
    tools = pins.list_tools(sys.executable, [str(pinned / "server.py")], 10)
    (pinned / pins.PINS).write_text(json.dumps({"servers": {"bench": {
        "command": sys.executable, "args": [str(pinned / "server.py")],
        "tools": {t["name"]: pins.tool_hash(t) for t in tools}}}}))
    penv = {**env, "BRAINRC_HOME": str(pinned)}
    fn = parallel(start, "{}", penv)
    outcome = json.loads((pinned / pins.LAST).read_text())["servers"].get("bench")
    if outcome != "same":  # the hook fails open, so check it really reached the server
        raise SystemExit(f"the pinned server wasn't checked: {outcome}")
    out.append(("Claude Code", "session start, 1 pinned server", len(start), fn))
    return out


def measure(runs: int) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        rows = []
        for tool, case, hooks, fn in cases(home):
            ms = timed(fn, runs)
            rows.append({"tool": tool, "case": case, "hooks": hooks, "runs": runs,
                         "median_ms": round(statistics.median(ms), 1), "p95_ms": round(percentile(ms, 95), 1)})
    hooks_python = subprocess.run(["python3", "-c", "import platform; print(platform.python_version())"],
                                  capture_output=True, text=True, check=False).stdout.strip()
    return {"os": f"{platform.system()} {platform.machine()}", "python": hooks_python, "rows": rows}


def table(result: dict) -> str:
    lines = [f"Hook latency on {result['os']}, hooks' python3 {result['python']}, "
             f"{result['rows'][0]['runs']} runs each",
             "", "| Tool | Call | Hooks | Median ms | p95 ms |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {r['tool']} | {r['case']} | {r['hooks']} | {r['median_ms']} | {r['p95_ms']} |"
              for r in result["rows"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", type=int, default=50, help="timed runs per case (after 3 warm-up runs)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a Markdown table")
    parser.add_argument("--summary", metavar="FILE", help="also append the table to FILE (CI's step summary)")
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    result = measure(args.runs)
    print(json.dumps(result, indent=2) if args.json else table(result))
    if args.summary:
        with open(args.summary, "a", encoding="utf-8") as f:
            f.write(table(result) + "\n\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
