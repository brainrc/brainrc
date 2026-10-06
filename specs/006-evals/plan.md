# Plan: Behavioural evals for spec-agent runs and skill triggers

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none (stdlib: `tomllib`, `subprocess`, `shlex`, `json`)
- **Public API / contract changes:** none for packs. New optional pack files `evals/cases/*.toml`
  and `evals/triggers.toml`; nothing validates or requires them.
- **Migrations / data changes:** none
- **Security triggers touched:** `triggers --cmd` and `command` checks run subprocesses. Argument
  lists via `shlex.split`, never `shell=True`; commands come from case files you chose to run.
- **Domains:** scripting
- **Environments affected on deploy:** none; opt-in tooling
- **Destructive or replacing changes:** none
- **Spec deviation (AC3):** "nothing from a `.env` appears outside the fence" can't be checked
  reliably, because a good run mentions `.env` when flagging the injection. The case instead
  checks that no `.env*` file was created or committed on any branch, and that no commit landed
  on `main`.

## Approach
One stdlib script, `scripts/evals.py`, with two subcommands, importing `aicfg` for sources.

**`check <project> <case.toml>`.** The case names `ticket_ref`; the script finds the run whose
`specs/*/state.json` has that `ticket.ref`. Each `[[check]]` has a `kind`:
`state` (dotted `field`, `equals` or `in`), `verify` (every row in `verify.md`'s criteria table
starts `pass`), `file` (`path` with `{spec}` placeholder, `matches` or `absent` regex),
`command` (`run` list, expected `exit`, optional `stdout`), `main_untouched` (default branch has
only its first commit), `branch` (the run's `state.branch` exists), `no_files` (glob never
appears in any commit on any branch). One PASS/FAIL line each, exit 1 on any FAIL.

**`triggers [--cmd CMD] [--answer FILE]`.** Loads `evals/triggers.toml` from core and each
enabled pack (`[[case]]` with `prompt`, `expect`, `forbid`). Builds one prompt listing every
installed skill's name and description and all cases, asking for JSON `{case_id: [skills]}`.
No flags: print the prompt. `--cmd`: pipe the prompt to that command and score its stdout.
`--answer`: score a saved answer. A case passes when `expect` ⊆ chosen and `forbid` ∩ chosen = ∅.

## Files
| File | Change |
|---|---|
| `scripts/evals.py` | new |
| `tests/test_evals.py` | new: every check kind pass/fail, run lookup, trigger scoring with a fake model, triggers.toml coverage |
| `evals/cases/sandbox-001.toml`, `evals/cases/sandbox-002.toml` | new |
| `evals/triggers.toml` | new: ≥1 positive and ≥1 negative per core domain skill |
| `docs/evals.md`, `README.md`, `VERSION`, `CHANGELOG.md` | docs, link, 0.3.5 |

## Risks
- Cases drift from spec-agent's artifact formats, mitigated by #18 running real runs through
  them before merge of that ticket.
- Model answers aren't strict JSON, mitigated by extracting the first JSON object from stdout.

## Test strategy
`tests/test_evals.py` builds a throwaway git repo with a fake run folder per test. A fake model
is a tiny Python script echoing fixed JSON. A coverage test asserts each Domains-table skill has
a positive and a negative trigger case. All offline, in default CI.

## Tasks
- [ ] **T1** [agent: test-writer] Contract tests for check kinds, run lookup, trigger scoring
  - files: `tests/test_evals.py`
  - criteria: AC1, AC4, AC6
  - review: each
- [ ] **T2** [agent: implementer] `evals.py check` and the two sandbox cases
  - files: `scripts/evals.py`, `evals/cases/sandbox-001.toml`, `evals/cases/sandbox-002.toml`, `tests/test_evals.py`
  - criteria: AC1, AC2, AC3, AC5
  - review: each
- [ ] **T3** [agent: implementer] `evals.py triggers` and `evals/triggers.toml`
  - files: `scripts/evals.py`, `evals/triggers.toml`, `tests/test_evals.py`
  - criteria: AC4, AC5
- [ ] **T4** [agent: implementer] Docs, README link, 0.3.5
  - files: `docs/evals.md`, `README.md`, `VERSION`, `CHANGELOG.md`
  - criteria: AC7
