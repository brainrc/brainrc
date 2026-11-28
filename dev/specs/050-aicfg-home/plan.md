# Plan: Render rules and extensions to $AICFG_HOME

Inline mode, tests first. One review pass before Verify.

| Task | What | Files | Criteria | Red test |
|---|---|---|---|---|
| T1 | `aicfg_home()`; `rendered_instructions()` and a new `home_extensions_file()` under it; `apply` writes both plus the deprecated in-repo `extensions.md`, removes `dist/instructions.md`; `_managed_target` knows `$AICFG_HOME/instructions.md`; doctor checks the home files; existing tests move off `dist/` | `scripts/aicfg.py`, `tests/test_aicfg.py` | AC1–AC3, AC5, AC7 | `AicfgHomeTest`: fake `AICFG_HOME`; apply writes both files there; a link to `dist/instructions.md` shows `UPDATE` then points home; old `dist/instructions.md` removed; doctor flags a stale home render; `AICFG_HOME` unset → `~/.config/ai-config` |
| T2 | spec-agent and ticket-jira read order; docs; tutorial and its run script | `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/{lifecycle,campaign}.md`, `skills/ticket-jira/SKILL.md`, `README.md`, `harnesses.toml`, `docs/{architecture,packs,troubleshooting,tutorial}.md`, `specs/013-tutorial/run-tutorial.sh` | AC4, AC6 | `validate`; run the tutorial script |
| T3 | VERSION 0.3.16, CHANGELOG (in-repo `extensions.md` deprecated), `aicfg plugin` | `VERSION`, `CHANGELOG.md`, `.claude-plugin/*` | AC7 | `validate` |

## Risks
- Tests must never write to the real `~/.config`: `TempRepoCase` sets `AICFG_HOME` to a temp dir.
- A real `apply` on this machine is part of verification only in a fake `HOME`.
