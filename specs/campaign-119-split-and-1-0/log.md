# Campaign gh:119 · split and 1.0 (E15, part 2)

## 2026-11-28T05:01:06Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:119 --shape ordered --dry-run`, worked by hand: the skill ships in
brainrc/gatework, which isn't installed in the build environment.

- Epic children: #171, #172, #173, #296 and #338 are closed (part 1). Open: #174 (pack API
  version), #175 (move specs/), #176 (release cadence and v1.0).
- Members: #174 and #175, as the brief asks. #176 is skipped: it stays for a later part.
- Shape: `ordered`, as the brief asks. Order: #174, #175, the epic's sub-issue order. No child
  has a `Depends on #N` line, so the source is `none`.
- Delivery: `sequential`. One branch is pushable here, so #175's PR opens from it once #174's
  has merged, with `main` merged in first.
- Starts from `main` at 6e45900 (v0.8.39).

## engine · Campaign gate · approved
The coordinator's brief passes on the maintainer's "Start E15 part 2". Recorded as approved on
that basis. Merging (each merge publishes a release) and closing issues stay with the maintainer.

## engine · gh:174 · Spec and Plan
- `PACK_API = "1.0"` in `brainrc/packapi.py`, apart from `VERSION`. Packs pin it with
  `requires_api = "^1"` (the brief's name; the issue wrote `pack_api`, and `requires_api` sits
  beside `requires_core`). Constraints gain `^`, which keeps the first nonzero part.
- The contract is read from what enforces it: the pack.toml and mcp/servers.toml schemas (keys,
  types and limits, not descriptions), the layout list, item kinds, agent models, the naming
  patterns and the validator names `plugins.py` reads. `docs/schemas/pack-api/1.0.json` freezes
  it, `FROZEN` holds its digest, and `tests/test_pack_api.py` fails when the live contract differs,
  a frozen file changes, or a MINOR bump drops an entry. `scripts/pack_api.py --write` freezes a
  new version.
- `requires_core` stays: alone, it is checked as before; beside `requires_api` it is ignored (older
  cores still read it). Only `validate --pack` warns that it is deprecated, so a pack's users never
  see a warning they can't act on; apply and core's own validate stay quiet about it.
- `new pack`, the importers' scaffold, the pack template and both example packs write
  `requires_api`. docs/packs.md#compatibility states what pack API 1 freezes and the policy (MINOR
  adds, MAJOR removes or changes, a deprecation warns for at least one core minor first).
- Not changed: `CHANGELOG.md`'s header still says packs pin `VERSION` (the release owns that
  file). Gatework and brainrc/packs still pin `requires_core`; each moves to `requires_api` in its
  own repo once this ships.
