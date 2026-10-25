# Log: 096-keep-mode-follow-symlinks

## engine · intake · done
2026-10-25T18:38:25Z

**Did:** Child 1 of campaign gh:92. Branch 096-keep-mode-follow-symlinks from main (campaign checkpoint 1ed6f5a). ticket.md from gh:96. Size standard (security trigger: writes a file that can hold secrets), mode fallback (installed agents link to a stale ~/projects/ai-config copy), domains: scripting, offline only.

**Evidence:**
- `python3 -m unittest discover -s tests` → 367 passed (baseline)
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** specs/096-keep-mode-follow-symlinks/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-25T18:39:46Z

**Did:** Wrote spec.md: 7 criteria (mode kept, symlinks followed, temp never looser, backups, dangling link), new living area aicfg-apply.

**Evidence:**
- `living_specs.py check` → would update specs/living/aicfg-apply.md

**Changed files:** specs/096-keep-mode-follow-symlinks/spec.md

**Open issues:** 1 open question (backup location for symlinked files; default beside target).

**Next:** Spec gate
