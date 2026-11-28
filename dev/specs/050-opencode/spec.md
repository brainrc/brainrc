# Spec: OpenCode gets real subagents

Ticket: gh:50 step 4 (refs) + gh:19 (closes) · Size: standard (render + link + doctor + docs) · Status: approved

## What a real OpenCode 1.18.35 showed (npm install, fake HOME)
- Copying our agents into `~/.config/opencode/agents/` makes **the whole config invalid**:
  `Expected object | undefined, got "Read, Grep, ..." tools`. OpenCode stops loading.
- A converted agent (`description`, `mode: subagent`, `permission: {bash: deny, ...}`) loads and
  `opencode agent list` shows it as a subagent; an extra `name:` key is accepted.
- Docs (sst/opencode `agents.mdx`): `tools` is deprecated for `permission`; keys `read`, `edit`
  (write/edit/apply_patch), `glob`, `grep`, `list`, `bash`, `task`, `webfetch`, `websearch`,
  `todowrite`, ...; `model` must be `provider/model-id`; a subagent without `model` uses the
  model of the agent that called it.

## Acceptance criteria
- **AC1** `apply` renders each agent (core and enabled packs) to
  `$AICFG_HOME/opencode/agents/<name>.md` (#19 said `dist/`; renders moved to `$AICFG_HOME` in
  0.3.16) and links it from `[opencode] agents = "~/.config/opencode/agents"`, selected by a new
  harness key `agents_format = "opencode"`.
- **AC2** Conversion: keep `description` and the body; add `mode: subagent`; map Claude tools to
  permissions: a tool the agent lacks becomes `deny` (`Read`→`read`+`list`, `Grep`→`grep`,
  `Glob`→`glob`, `Edit`/`Write`/`MultiEdit`/`NotebookEdit`→`edit`, `Bash`→`bash`,
  `WebFetch`→`webfetch`, `WebSearch`→`websearch`, `Task`→`task`, `TodoWrite`→`todowrite`); a tool
  it has is left out, so the user's own OpenCode permissions (allow or ask) apply. `model` is
  dropped (tiers don't map to provider IDs). An agent without `tools` gets no `permission`.
- **AC3** Stale handling: removed agents' renders and links are pruned; `doctor` reports a stale
  or missing render like it does `instructions.md`.
- **AC4** Tests with a fixture agent (conversion, render, link, prune); a real `opencode agent list`
  in a fake HOME loads all 9 core agents as subagents with the expected denies.
- **AC5** Docs: `docs/formats.md` and `docs/spec-agent.md` tables (OpenCode agents ✅), lossy fields
  (model, MCP tools) in `docs/formats.md`, roadmap item done, README if it mentions it.
  VERSION 0.3.19; CHANGELOG.

## Not in this step
- **Guard plugin**: an OpenCode plugin can block a call (throw) or answer an existing prompt
  (`permission.ask`), but can't force a prompt, so "ask before git push" becomes "deny" there.
  Needs its own decision; next PR.
- No-clone OpenCode install (npm plugin): later with packs as packages.
- #19's E2E sandbox run needs a model provider login on your account; not run here.
- Splitting `aicfg.py` into a package: separate refactor PR.

## Open questions
None.
