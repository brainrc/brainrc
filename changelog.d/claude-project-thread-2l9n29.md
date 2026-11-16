---
bump: patch
---
- `brainrc import` turns a CLAUDE.md or AGENTS.md into a pack: one rule per section, in order, each with a comment naming the file and lines it came from. Claude Code's whole-line `@path` imports are inlined in place, a brainrc project block is left out, and the pack is checked as `validate --pack` would. It goes to `$BRAINRC_HOME/imported/<name>` (or `--to`), and `--enable` adds it to `packs.local.toml` (#163).
- New `brainrc/scaffold.py`: the one writer of a pack's layout (pack.toml, rules, skills), all or nothing, for the importers now and `new pack` (#150) later.
