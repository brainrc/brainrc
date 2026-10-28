# Log: 209-brainrc-docs-wording

## engine · intake · done
2026-10-28T17:12:47Z
**Did:** Branch from main (v0.4.4), carrying #208's record. Owner: "I don't want alerted or decisions until deliver gate" → Spec and Plan auto-approved, open questions and any Callout take their defaults and are listed at the Deliver gate, which stops for the owner. Size: about 40 files mention the old names, mostly mechanical text and deliberate compatibility code; sized standard (not large/split) as the default under that instruction, to be listed at Deliver. Mode subagent, domain scripting, offline only.

## analyst · spec · done
8 criteria; the Done-when grep becomes a test against a closed allowlist (path + regex + reason, stale entries fail); tutorial run offline via specs/013-tutorial/run-tutorial.sh; 5 open questions with defaults (rename test_aicfg.py and internal identifiers; keep living spec file names; keep Codex markers, OpenCode guard link name, .git/aicfg-fetched.json; size standard).

## engine · Spec gate · auto-approved (owner: no decisions until Deliver)
2026-10-28T17:15:37Z

## engine · Spec gate approval withdrawn
living_specs.py check failed (text outside a requirement block), and the MODIFIED blocks hold shorthand ("brainrc replaces aicfg") instead of full requirement text, which apply would write over 12 living requirements. Back to the analyst.

## analyst · spec · done (revision)
Requirement changes fixed: full requirement text in each MODIFIED block. Engine: living_specs check exit 0; each MODIFIED block equals the living text except the tool name (and the dropped #209 sentence).

## engine · Spec gate · auto-approved (owner: no decisions until Deliver)
2026-10-28T17:16:48Z
