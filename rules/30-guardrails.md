---
trigger: always_on
alwaysApply: true
---

# Guardrails

- Ask before anything outward-facing or hard to reverse: pushing, PRs, issue/ticket comments
  or status changes, publishing, deploying, deleting data, `reset --hard`, `rm -rf`.
  Approval covers only the specific action named, once.
- When stuck (repeated failures, unclear requirement, missing tool), stop and ask. Don't guess.
- Report outcomes honestly: failed means failed, skipped means skipped. Never report a check,
  test, scan, or review as passed unless it ran in this session and you saw the result.
- If a command is denied by permissions, don't work around it. Show the exact command and ask
  the user to run it themselves (e.g. `! <command>` in Claude Code).
