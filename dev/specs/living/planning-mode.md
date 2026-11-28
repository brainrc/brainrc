# planning-mode

Turn a topic into proven, created tickets.

### Plan command and researcher
The system SHALL offer `/plan <topic>` (or `--plan`) that runs a `researcher` role to propose candidate tickets from the repo, and from the web only when enabled. (AC1, AC11)
_Last changed by 243-planning-mode._

### Proof requirement
A candidate SHALL be created only with proof (reproducing command and output, failing test, or spike commit) plus file:line links, re-verified offline; others SHALL be listed under "Needs evidence" in `plan-report.md`. (AC1, AC2, AC3, AC12)
_Last changed by 243-planning-mode._

### Dry run and cap
`--dry-run` SHALL create nothing; one plan SHALL offer at most 10 tickets. (AC4, AC10)
_Last changed by 243-planning-mode._

### Researcher trust boundary
The researcher SHALL NOT follow instructions found in content, and plan artifacts and created tickets SHALL NOT contain secrets or pasted untrusted text. (AC8, AC9)
_Last changed by 243-planning-mode._
