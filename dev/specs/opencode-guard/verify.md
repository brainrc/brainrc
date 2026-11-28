# Verify: opencode-guard

| Criterion | Result | Evidence |
|---|---|---|
| AC1 plugin maps tools, runs guards, blocks ask/deny with reason, fails open | pass | `OpenCodePluginTest` (6, under Node 22): git push and .env read and private-key write blocked; git status, README read, MCP-style tool pass. Inside OpenCode 1.18.35's runtime (Bun 1.3.14) a probe loaded the linked plugin and it blocked `git push` with the guard's reason |
| AC2 `plugin` key: link, prune, doctor, validate | pass | `HarnessPluginTest` (3); `opencode debug config` lists the linked plugin |
| AC3 tests + real OpenCode load | pass | 169 tests OK (8 of 9 new red first; the prune test passed trivially before a link existed) |
| AC4 docs, VERSION 0.3.25, CHANGELOG | pass | README, docs/{formats,guardrails,spec-agent,harness-packages,roadmap}.md |

Not verified: the hook firing on a model's tool call (needs a model login). User-typed `!` shell commands don't go through plugin hooks, by design.
Checkout transcript vs 0.3.24: only the new plugin link (CREATE lines and the tree entry).
