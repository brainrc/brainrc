#!/usr/bin/env python3
"""Metrics rollup across spec-agent runs: Markdown table by default, `--json` for tools.

Offline and read-only on run folders. ccusage is only invoked under `--ccusage`.
Exits 0 even when runs are skipped or ccusage is unavailable; only bad arguments fail.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retro_aggregate  # noqa: E402
import retro_ccusage  # noqa: E402
import retro_metrics  # noqa: E402

SCHEMA_VERSION = 1
UNKNOWN, NA = "unknown", "n/a"


def discover(roots: list) -> list:
    """(label, run_dir) for each state.json under `<root>/specs/*` (or `<root>/*` when root has
    no `specs` dir), once per resolved path. The label starts with the root as passed."""
    seen, found = set(), []
    for root in roots:
        base = Path(root) / "specs"
        if not base.is_dir():
            base = Path(root)
        label_base = os.path.join(root, "specs") if (Path(root) / "specs").is_dir() else root
        try:
            entries = sorted(base.iterdir())
        except OSError:
            print(f"warning: cannot read root {root}", file=sys.stderr)
            continue
        for run_dir in entries:
            state = run_dir / "state.json"
            if not state.exists():
                continue
            key = state.resolve()
            if key in seen:
                continue
            seen.add(key)
            found.append((os.path.join(label_base, run_dir.name), run_dir))
    return found


def run_dates(run_dirs: list) -> tuple | None:
    """(earliest, latest) UTC dates over the runs' started_at and stage_started_at values."""
    days = []
    for run_dir in run_dirs:
        try:
            metrics = json.loads((run_dir / "state.json").read_text(encoding="utf-8")).get("metrics")
        except (OSError, ValueError, AttributeError, RecursionError):
            continue
        if not isinstance(metrics, dict):
            continue
        stamps = [metrics.get("started_at")]
        stage = metrics.get("stage_started_at")
        stamps += list(stage.values()) if isinstance(stage, dict) else []
        for s in stamps:
            try:
                ts = datetime.fromisoformat(s)
            except (TypeError, ValueError):
                continue
            if ts.tzinfo is not None:
                days.append(ts.astimezone(timezone.utc).date())
    # ccusage buckets by local day, stamps are UTC: widen by a day each side
    return (min(days) - timedelta(days=1), max(days) + timedelta(days=1)) if days else None


def usage(requested: bool, dates: tuple | None) -> dict:
    if not requested:
        return {"requested": False, "available": False, "since": None, "until": None,
                "tokens": None, "cost": None, "note": "tokens unknown: run with --ccusage"}
    if dates is None:
        result = {"available": False, "since": None, "until": None, "tokens": None, "cost": None,
                  "note": "ccusage cost unavailable: reported runs have no dates"}
    else:
        result = retro_ccusage.period_totals(*dates)
    return {"requested": True, **result}


def build(roots: list, ccusage: bool) -> dict:
    records, skipped, dirs = [], [], []
    for label, run_dir in discover(roots):
        loaded = retro_metrics.load_run(run_dir, label)
        if isinstance(loaded, retro_metrics.Skipped):
            skipped.append(asdict(loaded))
        else:
            records.append(loaded)
            dirs.append(run_dir)
    return {
        "schema_version": SCHEMA_VERSION,
        "runs": [asdict(r) for r in records],
        "skipped": skipped,
        "aggregates": retro_aggregate.aggregate(records),
        "usage": usage(ccusage, run_dates(dirs) if ccusage else None),
    }


def _fmt(v, nd: int = 1) -> str:
    if v is None:
        return UNKNOWN
    if isinstance(v, float):
        return f"{v:.{nd}f}".rstrip("0").rstrip(".") if nd else f"{v:.0f}"
    return str(v)


def _pct(v) -> str:
    return UNKNOWN if v is None else f"{v * 100:.0f}%"


def _cell(v) -> str:
    return str(v).replace("|", "\\|").replace("\n", " ")


def _table(header: list, rows: list) -> list:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return lines


def _avg(a: dict, fmt=_fmt) -> str:
    return f"{fmt(a['avg'])} (n={a['n']})" if a["n"] else UNKNOWN


def _run_row(r: dict) -> list:
    stage = r["stage"] or UNKNOWN
    return [
        r["path"], r["size"] or UNKNOWN, r["mode"] or UNKNOWN,
        ", ".join(r["domains"]) if r["domains"] else UNKNOWN,
        stage, r["blocked_reason"] or "", _fmt(r["total_minutes"]), _fmt(r["agent_minutes"]),
        _fmt(r["wait_minutes"]), _pct(r["first_pass_rate"]), _fmt(r["retries"]),
        _fmt(r["interventions"]), _fmt(r["wave_ratio"], 2), r["criteria_passed"] or UNKNOWN,
        "; ".join(r["warnings"]),
    ]


def render_markdown(doc: dict) -> str:
    out = ["# Spec-agent metrics rollup", "", "Minutes unless noted. `unknown` means not recorded; "
           "it is never counted as 0.", "", "## Runs", ""]
    out += _table(["Run", "Size", "Mode", "Domains", "Stage", "Blocked", "Total min", "Agent min",
                   "Gate wait min", "First-pass", "Retries", "Interventions", "Wave ratio",
                   "Criteria", "Warnings"], [_run_row(r) for r in doc["runs"]])
    if doc["skipped"]:
        out += ["", "## Skipped runs", ""]
        out += _table(["Run", "Reason"], [[s["path"], s["reason"]] for s in doc["skipped"]])
    agg = doc["aggregates"]
    out += ["", f"## Aggregates ({agg['runs']} runs)", "",
            "Averages show n, the runs where the value is known. Duration averages use done runs only.", ""]
    groups = [("Overall", {"all": agg["overall"]}), ("By size", agg["by_size"]),
              ("By mode", agg["by_mode"]), ("By domain", agg["by_domain"]),
              ("By final stage", agg["by_stage"])]
    for title, rows in groups:
        out += [f"### {title}", ""]
        body = []
        for name, g in rows.items():
            a = g["averages"]
            body.append([name, g["runs"], _avg(a["total_minutes"]), _avg(a["agent_minutes"]),
                         _avg(a["wait_minutes"]), _avg(a["first_pass_rate"], _pct),
                         _avg(a["retries"]), _avg(a["interventions"]), g["blocked_stops"]["count"]])
        out += _table([title.replace("By ", "").capitalize(), "Runs", "Avg total", "Avg agent",
                       "Avg gate wait", "Avg first-pass", "Avg retries", "Avg interventions",
                       "Blocked stops"], body)
        if title == "By domain":
            out += ["", agg["domain_note"]]
        out.append("")
    blocked = agg["blocked_stops"]
    out += [f"### Blocked stops ({blocked['count']})", ""]
    out += [f"- {_cell(r)}" for r in blocked["reasons"]] or ["- none"]
    u = doc["usage"]
    out += ["", "## Tokens and cost", ""]
    if u["available"]:
        out += [f"Period total {u['since']} to {u['until']} (all sessions, not per run): "
                f"tokens {_fmt(u['tokens'])}, cost {_fmt(u['cost'], 2)}"]
    else:
        out += [f"Tokens: {UNKNOWN}. Cost: {NA}.", "", u["note"]]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="retro_report.py",
        description="Roll up metrics across spec-agent runs (offline, read-only).")
    p.add_argument("--root", action="append", metavar="DIR",
                   help="project root holding specs/*/state.json (or a specs dir itself); "
                        "repeatable; default: current directory")
    p.add_argument("--json", action="store_true", help="print one JSON document instead of Markdown")
    p.add_argument("--ccusage", action="store_true",
                   help="add period-total tokens and cost from `ccusage daily --json` (optional)")
    args = p.parse_args(argv)
    doc = build(args.root or ["."], args.ccusage)
    sys.stdout.write(json.dumps(doc, indent=2) + "\n" if args.json else render_markdown(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
