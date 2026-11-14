---
bump: patch
---
- `brainrc audit` lists, per harness, every skill, agent, command, rule, hook and MCP server
  brainrc puts there, with the pack it came from, the pack's commit, the item's sha256 and
  whether it's installed now, then each pack's permissions from brainrc.lock and the MCP tool
  pins. `--json` prints the same as JSON. It makes no network calls, writes nothing, and writes
  home paths with ~ (#291).
