# Campaign gh:117 · item scaffolders (E8), with E12's #166 and #167

## 2026-11-18T09:40:00Z · intake
`/brainrc-work --campaign gh:117 --shape ordered --dry-run`
- Members: gh:159 (`new skill`), gh:160 (`new agent`), gh:161 (`new rule`), gh:162
  (`new command`). All open; none skipped. The brief adds E12's last two importers, gh:166
  (Windsurf) and gh:167 (Claude Code plugin), recorded in specs/campaign-118-importers.
- Shape: `playbook`, batch 3, as the epic body names (over `--shape ordered`, per the brief's "use
  the shape the epic names"). gh:159 seeds `playbook.md`; the other three are its rows.
- Delivery sequential, on the one branch this run may push to: one draft PR to main, one commit
  per issue, in the brief's order 159, 160, 161, 162, 166, 167.
- The issue bodies name `aicfg/`; the package is `brainrc/`. Items are rendered by
  `brainrc/scaffold.py`, the writer `new pack` and `import` use.

## 2026-11-18T09:40:00Z · Campaign gate · auto-approved
Recorded as approved on the brief (passing on the maintainer's "Send E8 to coding"). Merging,
tagging and closing the epics stay with the maintainer.

## 2026-11-18T14:30:00Z · gh:159 to gh:162 verified
- `new skill|agent|rule|command <name>` find the pack upward (or take `--pack`), apply the prefix,
  refuse an existing item without `--force` (a rule never replaces one), write nothing on
  `--dry-run`, and check the pack after writing. Each issue's Done when is a test in
  tests/test_new_item.py run inside a pack made by `new pack`.
- Deviation within the playbook: `new command` can write a skill (`--as-skill`), so its output
  path depends on the option; the row's `{writes}` names the default.

## 2026-11-18T14:35:00Z · gh:166 and gh:167 verified (E12 playbook v1)
- Windsurf: a new `importers/windsurf.py`; trigger frontmatter maps as Cursor's does.
- Plugin: deviates from the E12 playbook, which maps to rules and skills only. The scaffold now
  writes agents, commands, `mcp/servers.toml` and other files (hook scripts, a skill's own files,
  executable bits kept), so a plugin moves over whole.

## 2026-11-18T14:40:00Z · Deliver gate · auto-approved
One draft PR, base main, one commit per issue. Next: code review, fixes, CI, then the maintainer
decides whether to merge. #117 and #118 stay open until then.
