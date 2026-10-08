# Spec: Record the #50 packaging spike

Ticket: gh:50 (refs; spike only) · Size: small (one new reference doc, README link) · Status: draft

## Problem
The per-harness research for #50 lives only in this session. The build tickets need it in the
repo, with sources and what's still unconfirmed.

## Acceptance criteria
- **AC1** `docs/harness-packages.md` (reference): one table row per harness (package format and
  install, rules without a clone, hooks and whether they can ask, agents, pack discovery), then a
  short section per harness with source links and every UNCONFIRMED item, and the evidence
  quality (Cursor and Codex docs sites were blocked here; findings came from search snippets,
  forums, and source code).
- **AC2** A "What this means" section: the Claude plugin format is shared by Codex (reads
  `.claude-plugin/`) and close to Cursor's; commands with `$ARGUMENTS` don't survive Codex;
  rules need `$AICFG_HOME`; ask isn't portable. Then the proposed ticket order for #50.
- **AC3** Linked from `docs/architecture.md` or the README; VERSION 0.3.15; CHANGELOG.
- **AC4** On approval at Deliver: a summary comment on #50 with the order; #50 stays open.

## Open questions
None.
