"""Helpers for a pack's own tests of its guard hooks (#138), so packs stop rebuilding the scaffolding.

A pack names its tests in pack.toml (`test = "tests"`) and `brainrc validate --pack` runs them with
this package importable:

    from brainrc.testing import assert_allows, assert_asks, assert_denies, assert_no_opinion

    HOOK = Path(__file__).resolve().parent.parent / "overrides/claude/hooks/guard_acme.py"

    class GuardTest(unittest.TestCase):
        def test_asks_before_a_deploy(self):
            assert_asks(HOOK, "acme deploy prod")      # the risky command
            assert_allows(HOOK, "acme deploy --help")  # and a safe near-miss

Each check runs the hook as Claude Code does: a PreToolUse payload as JSON on stdin, in a fresh
Python process. A string is a Bash command; a dict is the whole payload (another tool, say).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

__unittest = True  # a failing check's traceback ends in the pack's test, not here
DECISIONS = ("allow", "ask", "deny")


def bash(command: str) -> dict:
    """The PreToolUse payload for a Bash command."""
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def run_hook(hook: str | Path, payload: dict | str, timeout: float = 30) -> str | None:
    """The decision `hook` makes on `payload` ("allow", "ask" or "deny"), or None for no opinion
    (no output, or JSON with no permissionDecision). payload: a dict sent as JSON, or a str sent as
    is (to test a payload that isn't JSON). Exit code 2 is a block, so it reads as "deny"; a hook
    that is missing, fails, hangs or prints something else raises AssertionError."""
    name = Path(hook).name
    if not Path(hook).is_file():
        raise AssertionError(f"no hook at {hook}")
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    try:
        done = subprocess.run([sys.executable, str(hook)], input=stdin, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        raise AssertionError(f"{name} took over {timeout}s") from None
    if done.returncode == 2:
        return "deny"
    if done.returncode != 0:
        raise AssertionError(f"{name} exited {done.returncode}: {done.stderr.strip()}")
    out = done.stdout.strip()
    if not out:
        return None
    try:
        data = json.loads(out)
        decision = data.get("hookSpecificOutput", {}).get("permissionDecision")
    except (ValueError, AttributeError):
        raise AssertionError(f"{name} printed something that isn't hook JSON: {out!r}") from None
    if decision is not None and decision not in DECISIONS:
        raise AssertionError(f"{name} decided {decision!r}, not one of {', '.join(DECISIONS)}")
    return decision


def _check(hook: str | Path, cases: tuple, want: set, label: str) -> None:
    if not cases:
        raise AssertionError(f"no commands to check that {Path(hook).name} {label}")
    wrong = []
    for case in cases:
        try:
            got = run_hook(hook, bash(case) if isinstance(case, str) else case)
        except AssertionError as e:
            if not Path(hook).is_file():
                raise
            wrong.append(f"  {case!r}: {e}")
            continue
        if got not in want:
            wrong.append(f"  {case!r}: {got or 'no opinion'}")
    if wrong:
        raise AssertionError(f"{Path(hook).name} should {label}, but:\n" + "\n".join(wrong))


def assert_denies(hook: str | Path, *cases: str | dict) -> None:
    """Every case is denied (a "deny" decision, or exit code 2)."""
    _check(hook, cases, {"deny"}, "deny")


def assert_asks(hook: str | Path, *cases: str | dict) -> None:
    """Every case asks first."""
    _check(hook, cases, {"ask"}, "ask")


def assert_allows(hook: str | Path, *cases: str | dict) -> None:
    """No case is denied or asked about: the hook allows it or has no opinion."""
    _check(hook, cases, {"allow", None}, "allow")


def assert_no_opinion(hook: str | Path, *cases: str | dict) -> None:
    """The hook stays out of every case, so Claude Code's own permission check (and any later
    guard) still decides. Stricter than assert_allows, which also passes an "allow"."""
    _check(hook, cases, {None}, "have no opinion")
