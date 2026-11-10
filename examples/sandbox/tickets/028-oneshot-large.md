---
id: 28
title: Turn greet into a plugin platform (oneshot run)
status: open
pr:
---
Run with `--oneshot`. Rebuild the sandbox as an installable package with a plugin system for
greeting styles, a config file in the user's home directory, translations for ten languages, an
HTTP server that serves greetings as JSON, and a migration that converts old config files.

(Expected: sizes `large`. Oneshot does not stop here: the run splits the work into an ordered
campaign, runs the children `--oneshot` and stacked, and every PR opens ready, not draft.)
