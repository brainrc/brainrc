# Plan: Tutorial for your first domain skill and your first pack

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** none (docs)
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none
- **Deviation from the spec gate summary:** the tutorial starts a minimal pack from an empty
  directory instead of copying and renaming `examples/pack-acme`. Renaming every `acme` file
  and string needs `sed -i`, which behaves differently on macOS and Linux, and it drags in
  features (connector, tripwires, intake context) the reader doesn't need on day one. The
  example pack is the tutorial's "next step".

## Approach
`docs/tutorial.md` is one path with numbered steps. Each step has one `bash` block and a
"you should see" line. File contents are written with `cat > file <<'EOF'` inside the bash
blocks, so the whole tutorial is executable:

1. Clone core and run `validate` (baseline).
2. Create `~/src/myteam-ai-pack` with `pack.toml` (`name`, `prefix`, `requires_core`, one
   `[[extensions.domains]]` row for `*.proto` and `buf.yaml`).
3. Write `skills/myteam-protobuf/SKILL.md` in the four-section domain format.
4. `validate --pack` it, with one common error shown (missing prefix).
5. Enable in `packs.local.toml`, run `status`, then `apply`.
6. See it installed (`ls` in the harness skills dir) and listed for spec-agent (`grep` the
   rendered `extensions.md`), check cost with `aicfg tokens`.
7. Put the pack in git and add the CI snippet (`yaml` block, not executed).
8. Next steps: the example pack for the other features, and contributing a domain skill to core.

`specs/013-tutorial/run-tutorial.sh` extracts every `bash` block from the tutorial, swaps the
`<this-repo>` placeholder for the local checkout, and runs them in order with `HOME` set to a
temp directory, failing on the first error. So the check runs the doc itself, not a copy.

## Files
| File | Change |
|---|---|
| `docs/tutorial.md` | new |
| `specs/013-tutorial/run-tutorial.sh` | new: executes the tutorial's bash blocks |
| `README.md` | Adding content links the tutorial |
| `VERSION`, `CHANGELOG.md` | 0.3.3 |

## Risks
- The `requires_core` pin in the tutorial ages with every MINOR bump, mitigated by telling the
  reader to copy the range from `VERSION`, and by the script failing when it no longer matches.

## Test strategy
`run-tutorial.sh` exit 0 on a fresh clone in a temp HOME, plus `validate` and the suite.

## Tasks
- [ ] **T1** [agent: implementer] Write `docs/tutorial.md`
  - files: `docs/tutorial.md`
  - criteria: AC1, AC2, AC3
- [ ] **T2** [agent: implementer] `run-tutorial.sh` and a green run
  - files: `specs/013-tutorial/run-tutorial.sh`
  - criteria: AC4
- [ ] **T3** [agent: implementer] README link, 0.3.3
  - files: `README.md`, `VERSION`, `CHANGELOG.md`
  - criteria: AC5
