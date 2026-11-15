---
bump: patch
---
- Install-time check (#279): workflow `install-time` runs each install route (`uvx`, `pipx`, `npx`, `brew`) from scratch on ubuntu and macOS and fails one that takes over 60 seconds from the install command to the first `brainrc status`. `scripts/check_install_time.py` runs each route in a fresh temp HOME with empty caches. Pull requests time this checkout's build (wheel, sdist, packed repo, a formula for the local sdist in a scratch tap); the weekly run, and a manual run, time what's published, and a route whose source doesn't exist yet (no PyPI release, private repo, no tap, no Homebrew) prints SKIP, never PASS. It isn't a required check.
