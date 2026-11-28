# Log: 050-antigravity
- intake: owner said Gemini CLI was replaced by Antigravity CLI; confirmed (Google transition post, gemini-cli #27274). antigravity.google and the agy installer are blocked here; owner chose to build from public sources.
- spec: approved with hooks option A (none for now).
- plan: approved. T1 tests red (6), T2 aicfg, T3 rules + plugin.json, T4 real apply (identical render), T5 docs and release.
- after delivery: owner asked to replace every Gemini reference with Antigravity. Added an `antigravity` harness (`~/.gemini/config/`, from the agy CHANGELOG 1.2.15 and home-manager #10049); `gemini` kept disabled so `apply` prunes its links (checked: upgrade in a fake HOME from main's config removes 26 skill links and GEMINI.md, links 26 under `~/.gemini/config/skills`, doctor clean). The CHANGELOG history and one retirement line in harness-packages.md still name Gemini CLI.
