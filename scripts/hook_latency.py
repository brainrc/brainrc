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
CLAUDE = ROOT / "overrides" / "claude"
CURSOR_GUARD = ROOT / "overrides" / "cursor" / "hooks" / "guard.py"
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
    return ordered[max(0, -(-len(ordered) * pct // 100) - 1)] if ordered else 0.0


def hook_commands(event: str, tool: str | None = None) -> list[str]:
    """The fragment's commands for event (and tool, by each matcher as a full regex), with
    {{hooks_dir}} pointing at the checkout's hooks."""
    fragment = json.loads((CLAUDE / "settings.fragment.json").read_text())
    commands = []
    for group in fragment["hooks"].get(event, []):
        if tool is None or re.fullmatch(group.get("matcher", ".*"), tool):
            commands += [h["command"].replace("{{hooks_dir}}", str(CLAUDE / "hooks")) for h in group["hooks"]]
    return commands


def run(command: str, payload: str, env: dict) -> None:
    subprocess.run(["sh", "-c", command], input=payload, capture_output=True, text=True, env=env,
                   timeout=30, check=False)


def timed(fn, runs: int) -> list[float]:
    for _ in range(WARMUP):
        fn()
    out = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        out.append((time.perf_counter() - start) * 1000)
    return out


def claude_call(tool: str, tool_input: dict, env: dict):
    commands = hook_commands("PreToolUse", tool)
    payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input,
                          "cwd": "/tmp/project", "session_id": "bench"})

    def call():  # Claude Code runs the matching hooks of one call in parallel
        with ThreadPoolExecutor(len(commands)) as pool:
            list(pool.map(lambda c: run(c, payload, env), commands))
    return call, len(commands)


def cursor_call(event: dict, env: dict):
    payload = json.dumps(event)
    return lambda: run(f'python3 "{CURSOR_GUARD}"', payload, env)


def cases(home: Path) -> list[tuple[str, str, int, object]]:
    env = {**os.environ, "BRAINRC_HOME": str(home)}
    # The floor any Python hook pays: a shell and an interpreter that does nothing.
    out = [("Baseline", "sh + python3 -c pass", 0, lambda: run("python3 -c pass", "", env))]
    for name, tool, tool_input in CALLS:
        fn, hooks = claude_call(tool, tool_input, env)
        out.append(("Claude Code", name, hooks, fn))
    out.append(("Cursor", "shell command", 2, cursor_call(
        {"hook_event_name": "beforeShellExecution", "command": "git status"}, env)))
    out.append(("Cursor", "file read", 1, cursor_call(
        {"hook_event_name": "beforeReadFile", "file_path": "src/app.py"}, env)))
    start = hook_commands("SessionStart")
    session = lambda: [run(c, "{}", env) for c in start]  # noqa: E731
    out.append(("Claude Code", "session start, no MCP pins", len(start), session))
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
    out.append(("Claude Code", "session start, 1 pinned server", len(start),
                lambda: [run(c, "{}", penv) for c in start]))
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
    return {"os": f"{platform.system()} {platform.machine()}", "python": platform.python_version(), "rows": rows}


def table(result: dict) -> str:
    lines = [f"Hook latency on {result['os']}, Python {result['python']}, {result['rows'][0]['runs']} runs each",
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
