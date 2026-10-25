---
bump: patch
---
- spec-agent `watch` now handles unresolved PR review threads: a small ask becomes a fix task `R<n>`, a question gets a drafted reply, and a design-level ask stops for the user. Replies post via `reply_thread` only after approval at the Push gate, thread text is treated as untrusted (embedded instructions are flagged), each thread is handled once via `watch.thread_log`, and the PR is handed back after 3 review rounds. Post-merge verify remains planned.
