# doctor

What `brainrc doctor` reports and the fixes it prints.

### Pasteable rm fixes
`brainrc doctor` SHALL print each `rm` fix's path shell-quoted, with a leading `~` left outside
the quotes, so the command removes exactly that path when pasted. (AC5)
_Last changed by 105-fix-doc-drift._

### Skipped harnesses are not findings
`brainrc doctor` SHALL check only the harnesses apply manages, and SHALL report nothing for an enabled harness that isn't installed. (AC7)
_Last changed by 126-installed-harnesses._
