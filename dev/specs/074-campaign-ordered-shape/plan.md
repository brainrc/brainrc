# Plan: Campaign ordered shape

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** connector contract gains an optional read-only `dependencies` op (not added to `REQUIRED_CONNECTOR_OPS`, so packs keep validating); `campaign.json` gains `shape`, `dependency_source`, `members[].order/depends_on/branch`, status `waiting`; absent `shape` means `playbook`. `evals.py` gains kind `campaign`.
- **Migrations / data changes:** none · **Security triggers touched:** none (new `gh api` calls are GET only)
- **Domains:** scripting · **Environments affected on deploy:** none (offline repo config)
- **Destructive or replacing changes:** none

## Approach
Docs-driven engine change plus one eval kind. Shape selection reuses campaign.md step 1's three-member template check: it now picks `playbook` (shared template, no links) or `ordered` (differs, or any link), `--shape` overrides, and a playbook-shape template failure still lists deviants. Steps 2-4 stay playbook-only. A new final `## Ordered shape` section (one line at its top: "Playbook runs skip this section") covers ordering (Kahn topological sort, ties by epic order; cycle or out-of-epic link stops at the Campaign gate listing the links), per-child normal runs (own `specs/<slug>/`, Spec and Plan gates, branch from the previous child's branch, active-run pointer names the child in progress), one stack Deliver gate in merge order, sequential release (`main` merged in, tests re-run, PR body "N of M, after #X" + epic link), upstream-change propagation, pause on failure, and pull-only merge detection on resume. SKILL.md § Run step 1 and state.md § Resume carry the trigger lines so the engine reads them where it already looks.

Pinned shapes (every task quotes these verbatim):
- `dependencies` result, per child: `{ "source": "api" | "body" | "frontmatter" | "none", "depends_on": ["<ref>", ...] }`; refs use the same form as `members[].ref` (`gh:12`, `local:tickets/005-x.md`). GitHub: `gh api repos/<o>/<r>/issues/<n>/dependencies/blocked_by --jq '[.[].number]'`; on 404/unavailable (or MCP-only), lines matching `^Depends on #(\d+)` (case-insensitive) in the body via `gh issue view --json body` / `issue_read` `get`. Epic order for GitHub: `gh api repos/<o>/<r>/issues/<n>/sub_issues --jq '[.[].number]'` / `issue_read` method `get_sub_issues`. Merge state: `gh pr view <n> --json state` / `pull_request_read` `get` (read-only).
- Local frontmatter: `depends_on: [local:tickets/005-greet-name.md]` (flow list, refs relative to the project root; absent = none). Local epic: a ticket file with `children: [local:..., ...]` in frontmatter; the list order is the epic order (`list` returns them).
- `campaign.json` (ordered): `{ "ref": "<ref as given>", "shape": "ordered", "dependency_source": "<source>", "started_at": "<ISO>", "members": [ { "ref": "<ref>", "order": 1, "depends_on": [], "status": "delivered", "slug": "<slug>", "branch": "<slug>", "pr": "<PR URL, or branch name with no remote>" } ] }`. `members` keep epic order; `order` is 1-based build/merge order. Status adds `waiting` (verified and approved, PR not open until predecessor merges); after approval only `order: 1` is `delivered` with `pr` set, the rest `waiting` with `pr: null`.
- Eval: `find_campaign(project, ref)` globs `specs/campaign-*/campaign.json` matching `ref`; `cmd_check` falls back to it when `find_run` raises (run = campaign dir, state = campaign.json). Check `{ kind = "campaign", order = ["<ref>", ...] }` fails unless members sorted by `order` match `order`, each member's `specs/<slug>/state.json` has `gates.spec` and `gates.plan` == `approved`, and only the first member has `pr` set and status `delivered` (others `waiting`, `pr` null).

## Files
| File | Change |
|---|---|
| `scripts/evals.py`, `tests/test_evals.py` | `campaign` kind, `find_campaign`, fallback; tests |
| `skills/spec-agent/references/connectors.md`, `skills/ticket-local/SKILL.md`, `skills/ticket-github/SKILL.md` | `dependencies` op, local `depends_on:`/`children:`, sub-issue order |
| `skills/spec-agent/references/campaign.md`, `skills/spec-agent/SKILL.md`, `skills/work/SKILL.md` | shape selection, schema, `## Ordered shape`, `--shape` |
| `skills/spec-agent/references/state.md` | campaign resume, pointer in ordered campaign |
| `examples/sandbox/tickets/004-007*`, `examples/sandbox/README.md`, `evals/cases/sandbox-004.toml` | sandbox epic + eval case |
| `docs/spec-agent.md`, `changelog.d/074-campaign-ordered-shape.md` | both shapes; fragment (`bump: patch`) |

## Risks
- campaign.md grows past skimmable size, mitigated by keeping `## Ordered shape` under ~45 lines and last in the file.
- Parallel tasks drift on field names, mitigated by the pinned shapes above.

## Test strategy
AC18 unit tests in `tests/test_evals.py` (pass case; near-misses: wrong order, an unapproved plan gate, a second member delivered). AC13 via `sandbox-004.toml`, guarded by existing CaseFileTest (ticket exists, known kinds). Doc ACs checked by review against the pinned text; `validate` + unittest after each task.

## Tasks
- [ ] **T1** [agent: implementer] `campaign` check kind with `find_campaign` and `cmd_check` fallback, per the pinned Eval shape
  - files: `scripts/evals.py`, `tests/test_evals.py`
  - criteria: AC18
- [ ] **T2** [agent: implementer] Connector `dependencies` op (optional, read-only, pinned result), local `depends_on:`/`children:`, GitHub API + body fallback + sub-issue order + PR state read
  - files: `skills/spec-agent/references/connectors.md`, `skills/ticket-local/SKILL.md`, `skills/ticket-github/SKILL.md`
  - criteria: AC5, AC16, AC17
  - review: batch
- [ ] **T3** [agent: implementer] campaign.md: shape detection in step 1, gate states shape/order/source, pinned schema, `## Ordered shape` section; SKILL.md Run step 1 and work skill `--shape` + campaign resume
  - files: `skills/spec-agent/references/campaign.md`, `skills/spec-agent/SKILL.md`, `skills/work/SKILL.md`
  - criteria: AC1, AC2, AC3, AC4, AC6, AC7, AC8, AC9, AC10, AC11, AC12, AC15, AC17
  - review: batch
- [ ] **T4** [agent: implementer] state.md: Resume step for a campaign with `waiting` members (read predecessor PR state read-only, or user "merged"; no polling; see campaign.md § Ordered shape); pointer names the child in progress
  - files: `skills/spec-agent/references/state.md`
  - criteria: AC6, AC12, AC15
  - review: batch
- [ ] **T5** [agent: implementer] Sandbox epic `004-greeting-epic.md` (`children:` listed out of dependency order) and children 005 A, 006 B (`depends_on` A), 007 C (`depends_on` B), small dependent greet.py features; `sandbox-004.toml` with `campaign` order A,B,C + `main_untouched` + unittest command; README row
  - files: `examples/sandbox/tickets/004-greeting-epic.md`, `examples/sandbox/tickets/005-*.md`, `examples/sandbox/tickets/006-*.md`, `examples/sandbox/tickets/007-*.md`, `examples/sandbox/README.md`, `evals/cases/sandbox-004.toml`
  - criteria: AC13
  - after: T1
- [ ] **T6** [agent: implementer] docs/spec-agent.md short Campaigns section (both shapes, `--shape`, sequential PRs) and changelog fragment
  - files: `docs/spec-agent.md`, `changelog.d/074-campaign-ordered-shape.md`
  - criteria: AC14
  - review: batch
