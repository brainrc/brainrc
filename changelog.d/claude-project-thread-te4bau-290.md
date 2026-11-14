---
bump: patch
---
- `brainrc pin-mcp` approves the tools of the stdio MCP servers brainrc installs for Claude Code:
  it lists them, shows what changed, and on your yes records a hash of each tool definition in
  `$BRAINRC_HOME/mcp-pins.json`. A new SessionStart hook, `check_mcp_pins.py`, warns in the
  session and to the model when a pinned tool is changed, added or removed. It fails open within
  a 4-second budget and records each run's duration in `mcp-pins.last.json`. `apply` names the
  stdio servers whose tools aren't pinned (#290).
