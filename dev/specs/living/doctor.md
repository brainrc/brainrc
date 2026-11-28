# doctor

What `brainrc doctor` reports and the fixes it prints.

### Pasteable rm fixes
`brainrc doctor` SHALL print each `rm` fix's path shell-quoted, with a leading `~` left outside
the quotes, so the command removes exactly that path when pasted. (AC5)
_Last changed by 105-fix-doc-drift._

### Skipped harnesses are not findings
`brainrc doctor` SHALL check only the harnesses apply manages, and SHALL report nothing for an enabled harness that isn't installed. (AC7)
_Last changed by 126-installed-harnesses._

### Repair hint
`brainrc doctor` SHALL give `apply --repair` as the fix for a broken link that names the same item as the planned source, and `rm` plus `apply` for any other broken link. (AC6)
_Last changed by 129-apply-repair._

### Double install
`brainrc doctor` SHALL warn when the brainrc plugin (Claude Code's installed `brainrc@*`, unless disabled, or Cursor's `plugins/local/brainrc`) and brainrc's own links are both installed in that harness, naming which to remove. (AC1, AC2, AC3)
_Last changed by 130-doctor-plugin-overlap._
