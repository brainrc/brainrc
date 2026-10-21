# Evals

`validate` checks that files are well formed. Evals check behaviour: whether a spec-agent run
ended correctly, and whether skill descriptions make a model pick the right skills. Both live in
`scripts/evals.py` (stdlib only) and are opt-in, because a real eval needs a model run first.

## Grade a spec-agent run

Run a sandbox ticket ([examples/sandbox](../examples/sandbox/README.md)) to the end, leave the
run's branch checked out, then from the core checkout:

```bash
python3 scripts/evals.py check /tmp/spec-sandbox evals/cases/sandbox-001.toml
```

Each check prints `PASS` or `FAIL` with what it found, and any `FAIL` exits non-zero.
`sandbox-001` checks the happy path: gates approved, every criterion passed, tests green,
`--shout` works, default output unchanged, the spec's requirement delta applied to
`specs/living/`, nothing committed to `main`. `sandbox-002` checks that
the ticket's planted instructions were flagged in the spec and not followed, including that the
sandbox's decoy `.env` never leaked.

A case file names the run by `ticket_ref` and lists `[[check]]` entries. Kinds:

| Kind | Checks |
|---|---|
| `state` | a `state.json` field, by dotted path (a number indexes a list, e.g. `watch.ci_failures.0.cause`), `equals` a value, is `in` a list, or is `present` |
| `verify` | every criterion in `verify.md` is `pass` |
| `file` | a file (`{spec}` = the run folder) `matches` or has `absent` a regex |
| `command` | a command's `exit` code, and `stdout` if given |
| `main_untouched` | the default branch still has only its first commit |
| `branch` | the run's branch exists |
| `no_files` | no file matching `glob` was committed on any branch |
| `canary` | no value in `file` (default `.env`) appears in any commit or any file under `specs/` |
| `campaign` | an ordered campaign's `campaign.json` lists members in the `order` given, with Spec and Plan gates approved and only the first delivered |

## Check skill selection

AI tools load a skill when its description fits the request. `evals/triggers.toml` lists
requests with the skills a model should load (`expect`) and must not load (`forbid`).

```bash
python3 scripts/evals.py triggers > prompt.txt                       # paste into any model
python3 scripts/evals.py triggers --answer reply.txt                 # score its reply
python3 scripts/evals.py triggers --cmd "claude -p"                  # or pipe to a model CLI
```

The prompt lists every installed skill's name and description, core and enabled packs, and asks
for one JSON answer for all requests. This is a proxy: it tests the descriptions, not your tool's
own triggering, which a script can't observe. One `--cmd` run is one model call of about 2k tokens.

## Add evals from a pack

A pack can ship `evals/triggers.toml` (merged automatically when the pack is enabled) and
`evals/cases/*.toml` (pass the path to `check`). Give each domain skill a request that should
load it and a near miss that shouldn't.

The unit tests in `tests/test_evals.py` run in CI without a model: they grade fake run folders
and score a fake model's answers.
