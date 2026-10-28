Shipped: the tool is now `brainrc` (distribution, command, `import brainrc`, `python -m brainrc`, `scripts/brainrc.py`), and `brainrc --version` prints `brainrc <VERSION>`. The old `aicfg` names still work through 0.5.0 and each print one deprecation line on stderr.
Verify: `python3 -m unittest discover -s tests` and `python3 scripts/brainrc.py validate`. For the installed wheel, run `scripts/check_install.py` in a fresh venv (steps in the PR body).
Installed users: run `uv tool uninstall ai-config` (or `pipx uninstall ai-config`) before installing `brainrc`.
PR: <PR_URL>
