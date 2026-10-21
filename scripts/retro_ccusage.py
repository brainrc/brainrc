"""Optional ccusage period totals for retro_report. Stdlib only.

Runs `ccusage daily --json --since D --until D` (argument list, timeout, no shell) and returns
period totals. Any failure yields an "unavailable" result; nothing is raised to the caller.
"""
import json
import subprocess
from datetime import date


def _unavailable(since: date, until: date, reason: str) -> dict:
    return {
        "available": False,
        "since": since.isoformat(),
        "until": until.isoformat(),
        "tokens": None,
        "cost": None,
        "note": f"ccusage cost unavailable: {reason}",
    }


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("not a number")
    return value


def _totals(data) -> tuple:
    totals = data.get("totals")
    if isinstance(totals, dict):
        return _num(totals["totalTokens"]), _num(totals["totalCost"])
    daily = data["daily"]
    if not isinstance(daily, list):
        raise ValueError("daily is not a list")
    return (sum(_num(d["totalTokens"]) for d in daily),
            sum(_num(d["totalCost"]) for d in daily))


def period_totals(since: date, until: date, timeout: float = 30) -> dict:
    cmd = ["ccusage", "daily", "--json",
           "--since", since.strftime("%Y%m%d"), "--until", until.strftime("%Y%m%d")]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return _unavailable(since, until, "ccusage not found on PATH")
    except subprocess.TimeoutExpired:
        return _unavailable(since, until, f"ccusage timed out after {timeout:g}s")
    except OSError as exc:
        return _unavailable(since, until, f"could not run ccusage ({exc.strerror or exc})")
    if proc.returncode != 0:
        return _unavailable(since, until, f"ccusage exited with status {proc.returncode}")
    try:
        tokens, cost = _totals(json.loads(proc.stdout))
    except (ValueError, KeyError, TypeError, AttributeError):
        return _unavailable(since, until, "unexpected ccusage output")
    return {
        "available": True,
        "since": since.isoformat(),
        "until": until.isoformat(),
        "tokens": tokens,
        "cost": cost,
        "note": "period total for the date range, not per run",
    }
