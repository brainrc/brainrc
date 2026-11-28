# Playbook: one `brainrc new <kind>` per item kind

Campaign gh:117 (E8) · shape: playbook · version 1 · seeded by gh:159 (`new skill`).

Parameters: `{kind}` (skill, agent, rule, command), `{writes}` (the file it writes), `{extra}`.

## Steps
1. A `{kind}` branch in `render()` in `brainrc/newitem.py`, returning the files and the item's
   path; the text comes from `brainrc/scaffold.py` (`skill_text`, `agent_text`, `render_rule`,
   `command_text`), the same writer `new pack` and `import` use. No second scaffolder.
2. Its body in `brainrc/_templates/items/{kind}.md`: headings, one line each saying what goes there.
3. A subparser in `cli.py` (`item_help`), with only the options the kind takes.
4. Write through `scaffold.add_files` (refuses an existing file without `--force`, a path outside
   the pack and a path through a link), then run `validate --pack` on the pack.
5. Tests in `tests/test_new_item.py`, inside a pack made by `new pack`: the item validates with no
   warning, its name has the prefix once, and `{extra}` is covered.
6. docs/commands.md section (the doc test checks it against `--help`), a row in docs/packs.md
   § What `new <item>` writes, one changelog bullet.

## Verification
`python3 scripts/brainrc.py validate`; `python3 -m unittest discover -s tests`.

## Rollback
Remove the kind's subparser, `render()` branch and template; the other kinds don't use them.

## Review checklist
- Names meet docs/packs.md § Naming (prefix once, ASCII lowercase, length).
- Nothing written before every check has passed; `--dry-run` writes nothing.
- No model provider is called; stdlib only.
