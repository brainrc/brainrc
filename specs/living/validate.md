# validate

What `brainrc validate` checks in core and in packs beyond item frontmatter.

### Local tripwires
`brainrc validate` SHALL read an optional, gitignored `tripwires.local.toml` (`terms = [...]`) at
the core root and fail on every tracked core file whose path or text contains a term, compared
case-insensitively, naming the file, line and term; it SHALL fail when that file is tracked, and
SHALL skip untracked and per-machine `*.local.*` files. (AC1, AC2, AC3, AC4, AC5)
_Last changed by 104-local-tripwires._
