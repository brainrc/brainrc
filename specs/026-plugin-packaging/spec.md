# Spec: Claude Code plugin and marketplace

Ticket: gh:26 · Size: standard (generator in aicfg, two generated manifests, docs; design choices) · Status: draft

## What the plugin format covers (from the Claude Code docs and a `claude plugin validate` probe)
| ai-config piece | As a plugin |
|---|---|
| skills, agents, commands | yes: default `skills/`, `agents/`, `commands/` at the plugin root, which is this repo's layout |
| Claude guard hooks | yes: hooks in `plugin.json`, with `${CLAUDE_PLUGIN_ROOT}` in place of `{{hooks_dir}}`; no settings merge needed |
| rules (`dist/instructions.md`) | **no**: plugins can't ship always-loaded instructions |
| pack layering, `extensions.md`, other harnesses | **no**: `aicfg` only |
| version | `plugin.json` `version` = `VERSION` |
| `roles` symlink | inside the plugin root; `validate` accepts it |

Names get a plugin prefix: `/ai-config:work`, agent `ai-config:verifier`.

## Design choices
1. **The repo is both the marketplace and the plugin** (`"source": "."`), so users run
   `/plugin marketplace add bxker/ai-config` then `/plugin install ai-config@ai-config`.
2. **`aicfg plugin` generates `.claude-plugin/plugin.json` and `marketplace.json`**, committed so
   GitHub installs work. Name, description, version (`VERSION`), and hooks (from
   `overrides/claude/settings.fragment.json`, `{{hooks_dir}}` → `${CLAUDE_PLUGIN_ROOT}/overrides/claude/hooks`)
   all come from the repo. `validate` fails when the committed files differ from what
   `aicfg plugin` would write (run in CI), so they can't drift. Author is "ai-config
   contributors": no personal details.
3. **Rules stay `aicfg`-only.** The README says plugin users get skills, agents, commands, and
   hooks, and that rules need `aicfg` (or pasting `rules/` into their own CLAUDE.md).
4. **spec-agent finds its roles under either name.** In subagent mode, if `<role>` isn't an
   available agent, it uses `ai-config:<role>`.
5. **Pick one install path.** Plugin and `aicfg` together would load every skill and hook
   twice; README and `docs/troubleshooting.md` say so.
6. **Packs stay `aicfg` packs.** A pack's skills could ship as a plugin, but its spec-agent
   extensions (domains, ticket connector, Deliver checks) and rules need `aicfg` to render
   them. Recorded in `docs/packs.md`; revisit if plugins gain a way to extend another plugin.

## Acceptance criteria
- **AC1** `python3 scripts/aicfg.py plugin` writes both manifests from the repo; running it twice
  changes nothing.
- **AC2** `validate` fails, naming the file and the fix (`aicfg plugin`), when a committed
  manifest is missing or stale (e.g. after a `VERSION` bump).
- **AC3** `claude plugin validate .` passes on the branch (run locally, recorded in verify.md),
  with no warnings other than the root `CLAUDE.md` note.
- **AC4** README "Install as a Claude Code plugin" next to the `aicfg` path, with the
  what's-covered table and the pick-one note; `docs/packs.md` records the packs decision;
  `docs/troubleshooting.md` gets the double-install symptom.
- **AC5** spec-agent `SKILL.md`: the `ai-config:<role>` fallback in subagent mode.
- **AC6** Tests: generator output (version, hooks with `${CLAUDE_PLUGIN_ROOT}`, no `{{hooks_dir}}`
  left), idempotent, stale detection. VERSION 0.3.14 (the manifest's version follows), CHANGELOG.

## Open questions
None.
