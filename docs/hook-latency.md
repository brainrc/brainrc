# Hook latency and a native guard

The roadmap allows native hooks only on evidence (#299). This is the evidence, measured
against the owner's bar: if a tool call's p95 hook latency is over about 50 ms, port the guard
evaluator to Go; if it's under, stay in Python. A full rewrite is off the table either way.

## How it was measured

`scripts/hook_latency.py` runs the hooks each tool call fires the way the tool runs them: the
command from `overrides/claude/settings.fragment.json` through `sh -c`, a fresh `python3` per
hook, and the matching hooks of one Claude Code call in parallel. The `hook-latency` workflow ran
it with 100 runs per case (after 3 warm-ups) on GitHub's runners, Python 3.12, three times on
2026-11-16. Session start includes E28's MCP pin check, with one pinned local stdio server.

Median / p95 in ms. Linux is ubuntu-latest (x86_64), the steadiest of its three runs; macOS is
macos-latest (arm64), one column per run, because the runs disagree.

| Call | Hooks | Linux | macOS run 1 | macOS run 2 | macOS run 3 |
| --- | --- | --- | --- | --- | --- |
| Baseline: `sh` + `python3 -c pass` | 0 | 7.9 / 8.1 | 27.6 / 52.4 | 24.8 / 50.5 | 39.9 / 78.9 |
| Claude Code, Bash | 2 | 19.1 / 20.9 | 30.7 / 34.9 | 41.3 / 67.1 | 83.3 / 112.0 |
| Claude Code, Bash pipeline | 2 | 19.6 / 20.8 | 31.4 / 40.8 | 37.0 / 64.4 | 75.5 / 107.7 |
| Claude Code, Read | 1 | 18.6 / 19.3 | 28.5 / 29.9 | 37.5 / 61.2 | 67.7 / 110.8 |
| Claude Code, Edit | 1 | 19.2 / 19.9 | 28.6 / 32.0 | 41.3 / 66.4 | 70.8 / 96.2 |
| Claude Code, MCP tool | 1 | 15.7 / 16.5 | 26.0 / 28.1 | 41.1 / 69.5 | 48.9 / 87.8 |
| Cursor, shell command | 2 | 56.7 / 58.8 | 79.4 / 96.8 | 108.3 / 167.4 | 172.8 / 225.6 |
| Cursor, file read | 1 | 38.8 / 43.5 | 56.0 / 69.3 | 77.0 / 124.7 | 142.8 / 210.5 |
| Session start, no pins (once) | 1 | 26.2 / 28.0 | 35.5 / 36.8 | 48.7 / 77.0 | 78.4 / 105.1 |
| Session start, 1 pinned server (once) | 1 | 38.7 / 50.7 | 69.0 / 79.8 | 74.6 / 97.7 | 107.8 / 139.8 |

Across Linux's three runs, a Claude Code call's p95 stayed between 16 and 27 ms. Rerun with
`python3 scripts/hook_latency.py`, or the workflow on a pull request that touches the hooks.

## Against the 50 ms bar

- **Linux: under.** A Claude Code call's p95 is at most 27 ms in every run. About 8 ms of it is
  starting Python; the guard work is the rest.
- **macOS: over in two of three runs.** A Claude Code call's p95 was 28 to 41 ms in the first
  run, 61 to 70 ms in the second and 88 to 112 ms in the third.
- **Cursor: over everywhere,** because its `guard.py` starts a second Python for each guard.
- On macOS, most of the time is starting the interpreter, not the guard logic: an empty
  `python3 -c pass` alone had a p95 of 50 to 79 ms on those runners. The runners are shared VMs,
  so a developer's own Mac is likely faster, but these numbers are the evidence on hand.

## Outcome

By the bar, macOS is over, so **port the guard evaluator to Go**, and nothing else. For the
port to help, the hook a tool runs has to be the Go binary itself: a Python hook that calls a
Go evaluator still pays for starting Python, which is most of the time measured here. The
cheap Cursor fix (its guards in one process) is worth doing either way.

No Go work has started; it waits for the owner's go-ahead.
