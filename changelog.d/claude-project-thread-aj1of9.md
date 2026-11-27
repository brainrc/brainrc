---
bump: patch
---
- Native Windows hooks (#178): on Windows, `apply` writes each of brainrc's hooks as one Python call
  (`py -3 -X utf8 -I -c "..."`, falling back to `python`) instead of a POSIX shell line, in the field
  each tool's docs give for it: Claude Code's exec form, Codex's `commandWindows`, Copilot's
  `powershell`, and `command` for the rest. `doctor` checks the Windows line, and OpenCode's plugin
  runs its guards with `py -3` or `python` on Windows. macOS and Linux output is unchanged.
