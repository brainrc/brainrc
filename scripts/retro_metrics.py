"""Per-run metrics for spec-agent run folders.

`load_run` turns one `specs/<slug>/` folder into a `RunRecord` (every metric None when unknown)
or a `Skipped`. Fields follow skills/spec-agent/references/state.md. Missing is unknown (None),
never 0. Invalid timestamps add a warning and the affected values are None: nothing is clamped.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

STAGES = ("intake", "spec", "plan", "implement", "verify", "document", "deliver", "done")
GATE_STAGES = ("spec", "plan", "deliver")  # a gate's wait falls inside the stage of the same name


@dataclass
class Skipped:
    path: str
    reason: str


@dataclass
class RunRecord:
    path: str
    slug: str | None = None
    size: str | None = None
    mode: str | None = None
    domains: list | None = None
    stage: str | None = None
    blocked_reason: str | None = None
    total_minutes: float | None = None
    wait_minutes: float | None = None
    agent_minutes: float | None = None
    stage_minutes: dict | None = None
    gate_rework: dict | None = None
    first_pass_rate: float | None = None
    retries: int | None = None
    interventions: int | None = None
    waves: dict | None = None
    wave_ratio: float | None = None
    criteria_passed: str | None = None  # "n/m" or None
    blocked_stops: list | None = None  # one reason per stop: current block, then past log blocks
    warnings: list = field(default_factory=list)


def _int(v) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _num(v) -> float | int | None:
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _dict(v) -> dict | None:
    return v if isinstance(v, dict) else None


def _parse_ts(value, name: str, warnings: list) -> datetime | None:
    """Parse a UTC ISO timestamp. Missing is unknown (no warning); malformed warns."""
    if value is None:
        return None
    try:
        if not isinstance(value, str):
            raise ValueError
        ts = datetime.fromisoformat(value)
        if ts.tzinfo is None:
            raise ValueError
        return ts
    except ValueError:
        warnings.append(f"{name}: unparseable timestamp {value!r}")
        return None


def _minutes(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 60


def _gate_waits(metrics: dict, warnings: list) -> dict | None:
    """Wait minutes per gate, None for an invalid or incomplete gate; None if no gates recorded."""
    gates = _dict(metrics.get("gates"))
    if not gates:
        return None
    waits = {}
    for name, g in gates.items():
        g = _dict(g) or {}
        p = _parse_ts(g.get("presented_at"), f"gates.{name}.presented_at", warnings)
        a = _parse_ts(g.get("approved_at"), f"gates.{name}.approved_at", warnings)
        if p is None or a is None:
            waits[name] = None
        elif a < p:
            warnings.append(f"gates.{name}: approved_at before presented_at")
            waits[name] = None
        else:
            waits[name] = _minutes(p, a)
    return waits


def _stage_times(metrics: dict, warnings: list) -> dict:
    raw = _dict(metrics.get("stage_started_at")) or {}
    return {s: ts for s in STAGES if (ts := _parse_ts(raw.get(s), f"stage_started_at.{s}", warnings))}


def _per_stage(starts: dict, waits: dict | None, state_gates: dict, warnings: list) -> dict | None:
    present = [s for s in STAGES if s in starts]
    bad = set()
    for prev, nxt in zip(present, present[1:]):
        if starts[nxt] < starts[prev]:
            warnings.append(f"stage_started_at: {nxt} starts before {prev} (out of order)")
            bad.update((prev, nxt))
    if waits is None or len(present) < 2:
        return None
    out = {}
    for prev, nxt in zip(present, present[1:]):
        if prev in bad or nxt in bad:
            out[prev] = None
            continue
        if prev in GATE_STAGES:
            if prev in waits:
                wait = waits[prev]
            else:
                wait = 0 if state_gates.get(prev) == "skipped" else None
        else:
            wait = 0
        if wait is None:
            out[prev] = None
            continue
        mins = _minutes(starts[prev], starts[nxt]) - wait
        if mins < 0:
            warnings.append(f"stage {prev}: gate wait exceeds stage duration (negative minutes)")
            mins = None
        out[prev] = mins
    return out


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None


def _cells(line: str) -> list:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _verify_criteria(text: str) -> str | None:
    """"passed/total" from the Acceptance criteria table's Result column (found by header)."""
    section = text.split("## Acceptance criteria", 1)[1].split("\n## ", 1)[0] if "## Acceptance criteria" in text else ""
    result, rows = None, []
    for line in section.splitlines():
        cells = _cells(line)
        if result is None and "Result" in cells:
            result = cells.index("Result")
        elif result is not None and result < len(cells) and re.fullmatch(r"AC\d+", cells[0]):
            rows.append(cells[result])
    if not rows:
        return None
    return f"{sum(r.lower().startswith('pass') for r in rows)}/{len(rows)}"


def _retro_criteria(text: str) -> str | None:
    for line in text.splitlines():
        cells = _cells(line)
        if len(cells) >= 2 and cells[0] == "Criteria passed" and re.fullmatch(r"\d+/\d+", cells[1]):
            return cells[1]
    return None


def _criteria_passed(run_dir: Path) -> str | None:
    verify, retro = _read(run_dir / "verify.md"), _read(run_dir / "retro.md")
    return (verify and _verify_criteria(verify)) or (retro and _retro_criteria(retro)) or None


_HANDOFF = re.compile(r"## [^\n]+ \u00b7 [^\n]+ \u00b7 ([^\n \t]+)[ \t]*$")


def _log_handoffs(log: str) -> list:
    """(status, reason) per handoff header, oldest first.

    Reason is the first line of Open issues, else "unknown".
    """
    out = []
    for section in re.split(r"(?m)^(?=## )", log):
        m = _HANDOFF.match(section.split("\n", 1)[0])
        if not m:
            continue
        issues = re.search(r"(?m)^\*\*Open issues:\*\*[ \t]*(.*)$", section)
        reason = issues.group(1).strip() if issues else ""
        out.append((m.group(1), reason if reason and reason.lower() != "none" else "unknown"))
    return out


def _past_blocks(log: str, current) -> list:
    """Reasons of `blocked` handoffs. When state.blocked is set and the last handoff is blocked,
    that handoff is the current block (handoff.md), so it is not a past one."""
    handoffs = _log_handoffs(log)
    if current and handoffs and handoffs[-1][0] == "blocked":
        handoffs.pop()
    return [reason for status, reason in handoffs if status == "blocked"]


def load_run(run_dir: Path, label: str | None = None) -> RunRecord | Skipped:
    """Load `<run_dir>/state.json`. `label` is the path shown in output (default: run_dir)."""
    run_dir = Path(run_dir)
    label = label or str(run_dir)
    try:
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    except OSError as e:
        return Skipped(label, f"unreadable: {e.strerror or type(e).__name__}")
    except (ValueError, RecursionError) as e:  # JSONDecodeError and UnicodeDecodeError are ValueErrors
        return Skipped(label, f"invalid JSON: {e}")
    if not isinstance(state, dict):
        return Skipped(label, f"not a JSON object (got {type(state).__name__})")

    rec = RunRecord(path=label)
    for name in ("slug", "size", "mode", "stage"):
        v = state.get(name)
        setattr(rec, name, v if isinstance(v, str) else None)
    domains = state.get("domains")
    if isinstance(domains, list) and all(isinstance(d, str) for d in domains):
        rec.domains = domains
    blocked = state.get("blocked")
    if blocked:
        reason = blocked.get("reason") if isinstance(blocked, dict) else None
        rec.blocked_reason = reason if isinstance(reason, str) and reason else "unknown"

    log = _read(run_dir / "log.md")
    rec.blocked_stops = ([rec.blocked_reason] if rec.blocked_reason else []) + (_past_blocks(log, blocked) if log else [])
    rec.criteria_passed = _criteria_passed(run_dir)

    metrics = _dict(state.get("metrics")) or {}
    warnings = rec.warnings
    starts = _stage_times(metrics, warnings)
    began = _parse_ts(metrics.get("started_at"), "started_at", warnings)
    waits = _gate_waits(metrics, warnings)
    state_gates = _dict(state.get("gates")) or {}
    per_stage = _per_stage(starts, waits, state_gates, warnings)

    if rec.stage == "done":  # durations are only known for finished runs
        if began and "done" in starts:
            total = _minutes(began, starts["done"])
            if total < 0:
                warnings.append("total duration is negative (done before started_at)")
            else:
                rec.total_minutes = total
        if waits is not None and None not in waits.values():
            wait = sum(waits.values())
            if rec.total_minutes is not None and wait > rec.total_minutes:
                warnings.append("gate wait exceeds total duration: wait and agent time unknown")
            else:
                rec.wait_minutes = wait
                if rec.total_minutes is not None:
                    rec.agent_minutes = rec.total_minutes - wait
        rec.stage_minutes = per_stage

    rec.gate_rework = _dict(metrics.get("gate_rework"))
    reviews = _dict(metrics.get("reviews")) or {}
    total, first = _int(reviews.get("total")), _int(reviews.get("first_pass"))
    if total and first is not None:
        rec.first_pass_rate = first / total
    rec.retries = _int(metrics.get("retries"))
    rec.interventions = _int(metrics.get("interventions"))

    waves = _dict(metrics.get("waves"))
    if waves:
        rec.waves = {k: _num(waves.get(k)) for k in ("count", "max_width", "task_minutes", "wall_minutes")}
        task, wall = rec.waves["task_minutes"], rec.waves["wall_minutes"]
        if task is not None and wall:
            rec.wave_ratio = task / wall
    return rec
