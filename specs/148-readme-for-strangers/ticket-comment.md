The README now opens with what brainrc syncs (one config into Claude Code, Codex CLI, OpenCode, Antigravity CLI, and Cursor), then a quickstart, sample output, and a "Why not …" comparison. spec-agent moves below.
Verify: `python3 scripts/check_tutorial.py --readme` runs the quickstart in a temp HOME and should print `PASS step 1 quickstart`; `python3 -m unittest discover -s tests` should pass.
PR: <PR_URL>
