"""Aggregates over `RunRecord`s: groups, counts, averages with n, blocked stops.

Counts include every record. Each average uses only runs where the value is known (None is
skipped, 0 is known) and reports its n. Duration averages use done runs only.
"""
from __future__ import annotations

DOMAIN_NOTE = "A run with several domains counts under each, so domain rows can sum past the run count."
DURATION_METRICS = ("total_minutes", "wait_minutes", "agent_minutes")
OTHER_METRICS = ("first_pass_rate", "retries", "interventions", "wave_ratio", "time_to_merge")


def final_stage(r) -> str:
    if r.blocked_reason:
        return "blocked"
    return "done" if r.stage == "done" else "in progress"


def _avg(values: list) -> dict:
    known = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return {"avg": sum(known) / len(known) if known else None, "n": len(known)}


def _avg_by_key(dicts: list) -> dict:
    """Average each key across the dicts that carry it; None values are unknown."""
    keys = sorted({k for d in dicts if isinstance(d, dict) for k in d})
    return {k: _avg([d.get(k) for d in dicts if isinstance(d, dict)]) for k in keys}


def blocked_reasons(r) -> list:
    """One reason per stop from `blocked_stops` (it already lists the current block first)."""
    reasons = []
    for stop in r.blocked_stops or []:
        reason = stop.get("reason") if isinstance(stop, dict) else stop
        reasons.append(reason if isinstance(reason, str) and reason else "unknown")
    return reasons


def _group(records: list) -> dict:
    done = [r for r in records if r.stage == "done" and not r.blocked_reason]
    averages = {m: _avg([getattr(r, m) for r in done]) for m in DURATION_METRICS}
    averages.update({m: _avg([getattr(r, m) for r in records]) for m in OTHER_METRICS})
    reasons = [reason for r in records for reason in blocked_reasons(r)]
    return {
        "runs": len(records),
        "averages": averages,
        "stage_minutes": _avg_by_key([r.stage_minutes for r in done]),
        "gate_rework": _avg_by_key([r.gate_rework for r in records]),
        "blocked_stops": {"count": len(reasons), "reasons": reasons},
        "merged": sum(r.outcome == "merged" for r in records),
        "abandoned": sum(r.outcome == "abandoned" for r in records),
        "regressions": sum(r.post_merge == "regression" for r in records),
    }


def _grouped(records: list, keys) -> dict:
    buckets: dict = {}
    for r in records:
        for k in keys(r):
            buckets.setdefault(k, []).append(r)
    return {k: _group(v) for k, v in sorted(buckets.items())}


def aggregate(records: list) -> dict:
    overall = _group(records)
    return {
        "runs": len(records),
        "overall": overall,
        "by_size": _grouped(records, lambda r: [r.size or "unknown"]),
        "by_mode": _grouped(records, lambda r: [r.mode or "unknown"]),
        "by_domain": _grouped(records, lambda r: r.domains or ["none"]),
        "by_stage": _grouped(records, lambda r: [final_stage(r)]),
        "domain_note": DOMAIN_NOTE,
        "blocked_stops": overall["blocked_stops"],
    }
