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
The system SHALL deliver an ordered stack `sequential` (only the first PR after approval, each next PR after its predecessor merges) or `stacked` (all PRs at once, each based on the previous child's branch), chosen at the Deliver gate; before any child PR merges, `main` SHALL be merged into its branch, its tests re-run, and its base SHALL be `main`. Upstream review changes and failures propagate as before. (AC1, AC2, AC3)
_Last changed by 090-campaign-ordered-fixes._

### Merge detection
The system SHALL learn of a predecessor's merge by reading its PR state on resume, or from the user, and SHALL NOT poll. (AC15)
_Last changed by 074-campaign-ordered-shape._

### Campaign state fields
`campaign.json` SHALL record `shape`, `delivery`, `depends_on`, `order`, and statuses `verified` and `waiting`, in one documented home that each child's branch updates only for its own member. (AC4, AC5)
_Last changed by 090-campaign-ordered-fixes._

### Worktree fence
Before landing a wave task, the engine SHALL check with a tested offline helper that every changed path is inside the task's worktree and `files`, and that the main tree is unchanged, using `git -C <worktree>`. (AC7, AC8)
_Last changed by 090-campaign-ordered-fixes._

### Wave link ordering
The architect SHALL put a task that links to a file another task creates in a later wave. (AC6)
_Last changed by 090-campaign-ordered-fixes._

### Auto campaigns
An ordered campaign started with `--auto` SHALL auto-approve its Campaign gate and each child's Spec
and Plan gates, and deliver stacked draft PRs in dependency order. A child's hard stop SHALL pause
the later children. (AC7)
_Last changed by 216-work-auto-mode._
