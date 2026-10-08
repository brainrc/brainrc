# Spec: Antigravity installs ai-config as a plugin

Ticket: gh:50 (step 3 of 6; refs) · Size: standard (manifest, rules frontmatter, aicfg strip, docs) · Status: draft

## Background (public sources; nothing here was run against a real agy)
Google retired Gemini CLI for consumer accounts on 2026-06-18; Antigravity CLI (`agy`, Go,
closed source) replaced it. Extensions are now "plugins". Sources: Google's transition post
and gemini-cli discussion #27274; `google-antigravity/antigravity-cli` CHANGELOG and issues
(#403, #1053, #1059); plugin repos that document tested behavior (MemPalace INVESTIGATION.md,
CoalHearth v2.8.0, tested on agy 1.3.1).
- **Install:** `agy plugin install <git url>` stages the repo as a plugin; it needs
  `plugin.json` at the repo root. Its schema needs only `name` (extra keys may be rejected).
- **Layout:** `plugin.json`, `skills/<name>/SKILL.md`, `agents/*.md`, `rules/*.md`, `hooks.json`,
  `mcp_config.json`, all at the plugin root. No `commands/` (core has none since 0.3.17).
- **Rules:** every `rules/*.md` needs frontmatter with `trigger: always_on` (or another trigger);
  without it the file is **silently dropped**.
- **Hooks:** plugin `hooks.json` at the root; commands run from the plugin folder. `PreToolUse`
  gets `toolCall: {name, args}` (`run_command` → `args.CommandLine`) and must print a decision:
  `ask` shows an Approve/Deny prompt, `deny` blocks. An empty `{}` is reported to **deny every
  call**, and `allow` is documented as auto-approve. There is no known "no opinion" reply.
- Install may copy only the folders it recognises (#403); symlinks are likely dropped, like Codex.

## Acceptance criteria
- **AC1** `aicfg plugin` also writes a root `plugin.json` = `{"name": "ai-config"}`; `validate`
  fails when it's missing or stale (same check as `.claude-plugin/`).
- **AC2** Each core `rules/*.md` starts with `---\ntrigger: always_on\n---`. `aicfg` strips rule
  frontmatter everywhere it reads rules (rendered `instructions.md`, token budget), so other
  harnesses see the same text as before. A test covers the strip; `validate` fails if a core
  rule lacks a `trigger`.
- **AC3** No guard hooks for Antigravity in this step (see the open choice below). README says so
  and points to agy's own permission settings.
- **AC4** Docs: README gets an Antigravity install block with caveats (built from public docs, not
  run here; hooks not shipped; `disable-model-invocation` likely ignored). `docs/harness-packages.md`
  gets an Antigravity section replacing Gemini CLI (kept as a short retired note), the table and the
  proposed order updated. `docs/formats.md` and the roadmap rename Gemini where they mean the
  current Google CLI. AGENTS.md notes the rule frontmatter. VERSION 0.3.18; CHANGELOG.
- **AC5** Tests and both validates pass; `aicfg apply` in a fake HOME renders `instructions.md`
  with no `trigger:` lines.

## Not in this step
Guard hooks for agy (needs a live test of the "no opinion" reply). An aicfg `antigravity`
harness entry (global skills/rules paths differ between sources). Agent frontmatter mapping.
Verifying any of this with a real `agy`.

## Open choice
**Hooks:** (A, recommended) ship none now; add them after a live agy test. (B) ship the guards
answering `ask` when they have no objection: safe but may prompt on every shell command.
