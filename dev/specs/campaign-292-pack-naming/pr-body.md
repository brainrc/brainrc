## Why

Epic #292 (E29): a clear name is the cheapest trust signal a pack has, and the rules have to exist,
and be checked, before the pack registry opens. Core agents were also the only core items without
the `brainrc-` prefix.

## What changed

- **#293:** `docs/packs.md` § Naming states the seven rules and lists the official pack IDs
  (`brainrc/starter`, `review`, `go`, `terraform-aws`, `kubernetes`, `security-baseline`). The roadmap
  table isn't in this repo, so the IDs come from the open "Official pack" issues (#313 to #317, #323).
- **#294:** new `brainrc/naming.py`, run by `validate` and `apply`. It refuses `brainrc-`/`brainrc/` in
  non-official packs, a prefix that doesn't start with the owner from the new optional `pack.toml`
  key `id = "<owner>/<pack>"`, vendor names as a word of a name, prefix or ID, anything one or two
  edits from `brainrc` or an official ID, non-ASCII or uppercase names (pack, prefix, ID, agents,
  commands, MCP servers), and prefixes outside 2 to 24 characters. Rule 7 (prefix-scoped items)
  was already enforced. Each rejection has a near-miss test in `tests/test_pack_naming.py`.
- **#295:** the ten agents are now `brainrc-<name>`, and spec-agent, its plan template, references
  and docs name them (names only, no behaviour change). Each old name is a stub alias with the same
  tools and model until 0.7.0; `validate` checks the aliases and rejects a new unprefixed core agent.
- Record: `specs/campaign-292-pack-naming/` and one `specs/<slug>/` per issue.

Decisions to check:
- `bump: minor`, since packs that broke a rule now fail. That makes the release 0.6.0, which is also
  when the five skill aliases from 0.5.14 said they'd be removed. They're outside this epic, so
  they stay for now. The example packs pin `<0.7`.
- "Starts with the owner's handle" is read as `<owner>-`, so owner `jdoe` can't take `jdoex-`.
- The vendor list (20 names) and the verified-vendor map (empty until #333) live in `brainrc/naming.py`.
- Without signing (#319), a pack is official when its declared `id` is in the table.

## How to verify

```bash
python3 scripts/brainrc.py validate
python3 scripts/brainrc.py validate --pack examples/pack-acme
python3 -m unittest discover -s tests
python3 scripts/check_tutorial.py
```

Closes #293
Closes #294
Closes #295

## Checklist

- [x] Added one `changelog.d/<branch>.md` fragment (`bump:` + bullets); did not edit `VERSION` or `CHANGELOG.md`
- [x] `python3 scripts/brainrc.py validate`
- [x] `python3 -m unittest discover -s tests`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
