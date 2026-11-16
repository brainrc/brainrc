# Hook latency and a native rewrite

The roadmap allows a native rewrite of the hooks only on evidence (#299). This is the evidence
and the recommendation; the decision is the owner's.

## How it was measured

`scripts/hook_latency.py` runs the hooks each tool call fires the way the tool runs them: the
command from `overrides/claude/settings.fragment.json` through `sh -c`, a fresh `python3` per
hook, and the matching hooks of one Claude Code call in parallel. The `hook-latency` workflow ran
it with 100 runs per case (after 3 warm-ups) on GitHub's runners, Python 3.12, on 2026-11-16.
Session start includes E28's MCP pin check, with one pinned local stdio server.

| Call | Hooks | Linux median / p95 ms | macOS median / p95 ms |
| --- | --- | --- | --- |
| Baseline: `sh` + `python3 -c pass` | 0 | 8.4 / 8.5 | 27.6 / 52.4 |
| Claude Code, Bash | 2 | 21.6 / 22.1 | 30.7 / 34.9 |
| Claude Code, Bash pipeline | 2 | 21.7 / 22.4 | 31.4 / 40.8 |
| Claude Code, Read | 1 | 21.0 / 21.8 | 28.5 / 29.9 |
| Claude Code, Edit | 1 | 21.3 / 21.9 | 28.6 / 32.0 |
| Claude Code, MCP tool | 1 | 17.7 / 18.4 | 26.0 / 28.1 |
| Cursor, shell command | 2 | 65.3 / 66.5 | 79.4 / 96.8 |
| Cursor, file read | 1 | 45.7 / 46.5 | 56.0 / 69.3 |
| Session start, no pins (once per session) | 1 | 28.0 / 28.8 | 35.5 / 36.8 |
| Session start, 1 pinned server (once per session) | 1 | 42.9 / 43.9 | 69.0 / 79.8 |

Linux is ubuntu-latest (x86_64); macOS is macos-latest (arm64). Rerun with
`python3 scripts/hook_latency.py`, or the workflow by hand.

## What the numbers say

- A Claude Code tool call pays about 20 ms on Linux and 30 ms on macOS, with p95 under 41 ms.
  A model turn takes seconds, so the hooks add around 1% to a call.
- Most of it is starting the interpreter: 8 ms of the 21 ms on Linux, and nearly all of it on
  macOS. The guard logic itself is a few milliseconds.
- So a **compiled guard evaluator** called from the Python hooks would save only those few
  milliseconds. A **Go rewrite** of the hooks would save the interpreter start too, about 15 to
  25 ms per call, at the cost of a second language, per-platform binaries, and a release and
  signing pipeline for them.
- The slowest path is Cursor's `guard.py`, which starts a second Python for each guard (65 to
  80 ms). Running the guards in the same process would roughly halve it, with no rewrite.
- Session start with real MCP servers is dominated by the servers themselves (npx and the like),
  which #357 covers; a native hook wouldn't change that.

## Recommendation

**No-go** on both a Go rewrite and a compiled guard evaluator for now. Do the cheap fix instead
(Cursor's guards in one process), and keep E31's adapter interface in Python. Look again if a
call's p95 passes 100 ms on either OS, or a supported tool starts running hooks on every
keystroke or file event.

## Decision

Pending. Question for the owner: go or no-go on a Go rewrite, or on a compiled guard evaluator
only?
