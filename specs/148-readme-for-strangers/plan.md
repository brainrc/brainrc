# Plan: Rewrite the README for strangers

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none (new `--readme` flag on the dev-only `scripts/check_tutorial.py`)
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting (offline only)
- **Environments affected on deploy:** none; CI's existing tutorial step gains one line
- **Destructive or replacing changes:** none

## Approach
Extend `scripts/check_tutorial.py` rather than add a near-copy script. Add `--readme [PATH]`
(default `README.md`): `parse_readme(text)` returns `{1: ("quickstart", block)}` from the first
```` ```bash ```` block under `## Quickstart`, dropping `git clone` lines exactly as `parse()` does
for step 1. Factor the body of `main()`'s loop into `run(parsed, expected) -> bool` so both modes
share `COPY_IGNORE`, the temp `HOME`/`USERPROFILE`/`BRAINRC_HOME`, the copied checkout at
`<tmp>/home/brainrc`, the timeout, and the PASS/FAIL report. `EXPECTED_README` holds only stable
lines (spec OQ4): ``Dry run. Run `apply` to write.`` (first `status` on a fresh HOME, from
`brainrc/cli.py`) and `Everything in sync.` (the confirming `status` after `apply`). A unit test
asserts each pattern also appears in README.md, so the check and the transcript stay coupled.
CI: add `python3 scripts/check_tutorial.py --readme` beside the tutorial step (OQ3: unit test
plus CI, both through the shared function).

README order: lead (five harnesses from `harnesses.toml`; skills everywhere, other kinds partial,
link `docs/formats.md#harness-support`) → Quickstart (clone, `status`, `apply`, `status`; one line
each on "status writes nothing" and "Everything in sync. means it worked") → Install (plugin
path kept verbatim, `/plugin install brainrc@brainrc`, link docs/install.md) → sample output →
Why not … table → spec-agent (three gates, `/work` example, harness callout unchanged) → More
(absorbs "Try it" links) → Contributing / Security / Privacy unchanged. Hard cap 100 lines.

Transcript (AC5): implementer runs the quickstart with `HOME`/`BRAINRC_HOME` under the
scratchpad (never the real HOME), keeps ~8 representative lines plus the final lines, and
greps it for `/home/`, `/Users/`, `@`, and the hostname before pasting. Comparison cells (AC7):
from each project's own docs via WebFetch if available; otherwise phrase conservatively from
the market-map research notes and list every such cell in the PR body for a reviewer check.
Add "Also see ruler, dotagents" one-liner (OQ2 default). Asciinema stays a follow-up (OQ1).

## Files
| File | Change |
|---|---|
| `scripts/check_tutorial.py` | modify: `--readme`, `parse_readme`, shared `run()` |
| `tests/test_check_tutorial.py` | modify: README parse, coupling, e2e tests |
| `.github/workflows/validate.yml` | modify: one step running `--readme` |
| `README.md` | rewrite per order above |
| `changelog.d/148-readme-for-strangers.md` | new: `bump: patch` |

## Risks
- 100-line cap is tight, mitigated by trimming the transcript and folding "Try it" into More.
- Unfair or stale comparison claims, mitigated by doc-linked, conservative cells and reviewer list.
- Transcript leaks a path or host, mitigated by temp HOME capture plus grep before paste.

## Test strategy
Unit tests in `tests/test_check_tutorial.py`: `parse_readme` on a fixture (block found, clone
dropped, missing section raises); `main(["--readme", edited])` fails on a broken command and on
missing expected output; e2e on the real README passes and leaves the caller's HOME empty;
every `EXPECTED_README` pattern is present in README.md. Existing `test_project_files.py` and
`test_plugin_docs.py` guard AC9. Final: validate, unittest, `check_tutorial.py` and `--readme`.

## Tasks
- [ ] **T1** [agent: implementer] README quickstart check: `--readme`, `parse_readme`, shared `run()`, fixture-based tests, CI step
  - files: `scripts/check_tutorial.py`, `tests/test_check_tutorial.py`, `.github/workflows/validate.yml`
  - criteria: AC4, AC10
- [ ] **T2** [agent: implementer] README lead, Quickstart, Install, real-run transcript, spec-agent moved below; real-README e2e and coupling tests; changelog fragment
  - files: `README.md`, `tests/test_check_tutorial.py`, `changelog.d/148-readme-for-strangers.md`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC8, AC9, AC10
  - after: T1
- [ ] **T3** [agent: implementer] "Why not …" table (chezmoi, GNU stow, harness plugins/marketplaces, rulesync; linked, no stars, brainrc's limits row), ruler/dotagents note
  - files: `README.md`
  - criteria: AC6, AC7, AC9
  - after: T2
