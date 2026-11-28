Spike results are in `docs/harness-packages.md` (linked PR, 0.3.15).

| Harness | Package | Rules without a clone | Hooks | Packs |
|---|---|---|---|---|
| Claude Code | `.claude-plugin/` (shipped) | `SessionStart` hook output | allow, ask, deny | plugin `dependencies` |
| Codex | `.codex-plugin/` or our `.claude-plugin/` | no plugin route (`~/.codex/AGENTS.md`) | yes, no reliable ask | separate plugin |
| Gemini CLI | `gemini-extension.json` | extension `GEMINI.md` | deny only | separate extension |
| OpenCode | JS plugin (hooks only) + config dir | `instructions[]` | block only | config arrays |
| Cursor | `.cursor-plugin/` (evidence weak) | via plugin | allow, deny | marketplace |

Proposed order: 1) render to `$AICFG_HOME`; 2) Codex via the existing `.claude-plugin/` (commands become skills: Codex skips `$ARGUMENTS`); 3) Gemini extension; 4) OpenCode (includes #19); 5) Cursor, after confirming its format; 6) packs as packages. Unconfirmed items are marked in the doc.
