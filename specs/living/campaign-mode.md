# campaign-mode

Run a set of related tickets as one campaign, in `playbook` or `ordered` shape.

### Shape selection
The system SHALL detect the shape (template check plus depends-on links), show it at the Campaign gate, and honor `--shape`, including `ordered` on an epic with no links (sub-issue order). (AC1, AC2, AC17)
_Last changed by 074-campaign-ordered-shape._

### Dependency order
The system SHALL order ordered-shape children topologically and stop at the Campaign gate on a cycle or out-of-epic link. (AC3, AC4)
_Last changed by 074-campaign-ordered-shape._

### Per-child gates and stack delivery
The system SHALL give each ordered child its own Spec and Plan gates, build on the predecessor's branch, and present one Deliver gate for the stack. (AC6, AC7)
_Last changed by 074-campaign-ordered-shape._

### Sequential PRs
The system SHALL open only the first PR after approval and each next PR after its predecessor merges, with `main` merged in and tests re-run; upstream review changes and failures propagate as in AC10 and AC11. (AC8-AC11)
_Last changed by 074-campaign-ordered-shape._

### Merge detection
The system SHALL learn of a predecessor's merge by reading its PR state on resume, or from the user, and SHALL NOT poll. (AC15)
_Last changed by 074-campaign-ordered-shape._

### Campaign state fields
`campaign.json` SHALL record `shape`, `depends_on`, `order`, and status `waiting`. (AC12)
_Last changed by 074-campaign-ordered-shape._
