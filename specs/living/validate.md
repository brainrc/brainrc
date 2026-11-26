# validate

What `brainrc validate` checks in core and in packs beyond item frontmatter.

### Local tripwires
`brainrc validate` SHALL read an optional, gitignored `tripwires.local.toml` (`terms = [...]`) at
the core root and fail on every tracked core file whose path or text contains a term, compared
case-insensitively, naming the file, line and term; it SHALL fail when that file is tracked, and
SHALL skip untracked and per-machine `*.local.*` files. (AC1, AC2, AC3, AC4, AC5)
`validate --local-tripwires FILE` SHALL read the terms from FILE instead, and fail when FILE is
missing or lists no term. When `GITHUB_ACTIONS` is `true`, a match SHALL name its file, line and
term number but never the term, and a term in a path SHALL show as `***`. CI SHALL run the check on
every push to `main` and every pull request that can read the `TRIPWIRE_TERMS` secret, and SHALL
skip with a notice when that secret is unset or empty. (#344)
_Last changed by 344-tripwires-ci._

### Pack naming rules
`brainrc validate` SHALL refuse a pack whose names break docs/packs.md § Naming, and `apply` SHALL
refuse to link it. (AC1 to AC7)
_Last changed by 294-validate-naming._
