#!/usr/bin/env python3
"""evals: behavioural checks for spec-agent runs and skill descriptions (docs/evals.md).

Usage:
  evals.py check <project-dir> <case.toml>   grade a finished spec-agent run against a case
  evals.py triggers [--cmd CMD] [--answer FILE] [--file TOML ...]
                                             without flags, print the skill-selection prompt;
                                             --cmd pipes it to a model CLI and scores the reply;
                                             --answer scores a saved reply

Stdlib only. Nothing here calls a model unless you pass --cmd.
"""
from __future__ import annotations

import fnmatch
import json
import re
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KINDS = ("state", "verify", "file", "command", "main_untouched", "branch", "no_files")


class EvalError(Exception):
    pass


# ---------- check ----------

def _git(project: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=project, capture_output=True, text=True)
    if result.returncode != 0:
        raise EvalError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def find_run(project: Path, ref: str) -> Path:
    """The specs/<slug>/ folder whose state.json names this ticket ref."""
    for state in sorted(project.glob("specs/*/state.json")):
        if json.loads(state.read_text()).get("ticket", {}).get("ref") == ref:
            return state.parent
    raise EvalError(f"no run found for ticket_ref {ref!r} under {project}/specs/")


def _field(data: dict, dotted: str):
    for key in dotted.split("."):
        data = data.get(key) if isinstance(data, dict) else None
    return data


def _criteria(verify: str) -> list[tuple[str, str]]:
    """(criterion, result) rows from verify.md's Acceptance criteria table."""
    section = verify.split("## Acceptance criteria", 1)[-1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(r"AC\d+", cells[0]):
            rows.append((cells[0], cells[-1]))
    return rows


def run_check(check: dict, project: Path, run: Path, state: dict) -> tuple[bool, str]:
    kind = check.get("kind")
    if kind == "state":
        value, field = _field(state, check["field"]), check["field"]
        allowed = check["in"] if "in" in check else [check["equals"]]
        return value in allowed, f"state {field} = {value!r}" + ("" if value in allowed else f", expected {allowed}")
    if kind == "verify":
        if not (run / "verify.md").is_file():
            return False, "verify: no verify.md in the run"
        rows = _criteria((run / "verify.md").read_text())
        bad = [ac for ac, result in rows if not result.lower().startswith("pass")]
        if not rows:
            return False, "verify: no criteria rows in verify.md"
        return not bad, f"verify: {len(rows)} criteria" + (f", not passed: {', '.join(bad)}" if bad else " all pass")
    if kind == "file":
        rel = check["path"].replace("{spec}", str(run.relative_to(project)))
        path = project / rel
        text = path.read_text() if path.is_file() else ""
        if "matches" in check:
            ok = bool(re.search(check["matches"], text, re.M))
            return ok, f"file {rel} {'matches' if ok else 'does not match'} {check['matches']!r}"
        ok = not re.search(check["absent"], text, re.M)
        return ok, f"file {rel} {'has no' if ok else 'contains'} {check['absent']!r}"
    if kind == "command":
        result = subprocess.run(check["run"], cwd=project, capture_output=True, text=True, timeout=120)
        want = check.get("exit", 0)
        if result.returncode != want:
            return False, f"command {' '.join(check['run'])}: exit {result.returncode}, expected {want}"
        if "stdout" in check and result.stdout != check["stdout"]:
            return False, f"command {' '.join(check['run'])}: stdout {result.stdout!r}, expected {check['stdout']!r}"
        return True, f"command {' '.join(check['run'])}: exit {want}"
    if kind == "main_untouched":
        branch = check.get("branch", "main")
        count = int(_git(project, "rev-list", "--count", branch).strip())
        return count == 1, f"{branch} has {count} commit(s), expected only the initial one"
    if kind == "branch":
        name = state.get("branch", "")
        ok = bool(name) and bool(_git(project, "branch", "--list", name).strip())
        return ok, f"branch {name!r} {'exists' if ok else 'missing'}"
    if kind == "no_files":
        names = set(_git(project, "log", "--all", "--name-only", "--format=").split())
        hits = sorted(n for n in names if fnmatch.fnmatch(Path(n).name, check["glob"]))
        return not hits, f"no_files {check['glob']!r}" + (f": committed {', '.join(hits)}" if hits else ": none committed")
    return False, f"unknown check kind {kind!r} (known: {', '.join(KINDS)})"


def cmd_check(project: str, case: str) -> int:
    root = Path(project).resolve()
    spec = tomllib.loads(Path(case).read_text())
    try:
        run = find_run(root, spec["ticket_ref"])
        state = json.loads((run / "state.json").read_text())
        results = [run_check(c, root, run, state) for c in spec.get("check", [])]
    except (EvalError, OSError, KeyError, subprocess.TimeoutExpired) as e:
        print(f"ERROR {e}")
        return 1
    for ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'} {detail}")
    failed = sum(not ok for ok, _ in results)
    print(f"\n{len(results) - failed} passed, {failed} failed ({Path(case).name} on {run.relative_to(root)})")
    return 1 if failed else 0


# ---------- triggers ----------

def score(cases: list[dict], answer: dict) -> list[tuple[str, bool, str]]:
    return []


def build_prompt(skills: dict[str, str], cases: list[dict]) -> str:
    return ""


def parse_answer(text: str) -> dict:
    return {}


def cmd_triggers(cmd: str | None = None, answer: str | None = None, files: list | None = None) -> int:
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "check":
        return cmd_check(argv[2], argv[3])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
