# Campaign gh:113 · Epic E6: open-source readiness

## engine · Campaign gate · auto-approved (oneshot)
2026-11-03T05:39:54Z

Shape: ordered (`--shape ordered`). Dependency source: none (no issue links; order is the epic's sub-issue order).
Order: 1 #146 project files · 2 #147 CI matrix, lint and types · 3 #148 README for strangers · 4 #149 namespace core skills.
Delivery: stacked, ready PRs (`--oneshot`). Each child runs its own Spec and Plan gates, auto-approved. Never merged or retargeted by the engine.

## 2026-11-03T05:58:40Z · child 1 gh:146 verified

## 2026-11-03T06:24:09Z · child 2 gh:147 verified
- Spec reworked once (tutorial steps 1-5). Infra HIGH (check name) fixed with a gate job.

## 2026-11-03T13:18:58Z · child 3 gh:148 verified

## 2026-11-03T13:21:05Z · child 4 gh:149 split (size large)
- 3 local children appended as members 5-7: 149.1 namespaced skills + aliases, 149.2 reserved-name check, 149.3 docs and changelog. Stacked after gh:148. The gh:149 issue closes with the last child.

## 2026-11-03T13:39:15Z · member 5 (149.1) verified

## 2026-11-03T13:45:22Z · member 6 (149.2) verified

## 2026-11-03T13:56:45Z · member 7 (149.3) verified · all members verified

## engine · stack Deliver gate · auto-approved (oneshot)
2026-11-03T13:57:23Z

⛔ Stack Deliver gate: campaign gh:113, 6 verified children, delivery stacked, ready PRs.
Outward actions:
1. `git push -u origin <branch>` for 146-oss-project-files, 147-ci-matrix, 148-readme-for-strangers, 149-1-namespaced-skills, 149-2-reserved-names, 149-3-docs-new-names (149-namespace-core-skills is not pushed: its spec commits ride in 149.1's PR).
2. Ready PRs, bodies from each child's pr-body.md (title = first line; `<PREV_PR>` and "N of 6" filled at open): #146 child → base main; #147 → base 146-oss-project-files; #148 → base 147-ci-matrix; 149.1 → base 148-readme-for-strangers; 149.2 → base 149-1-namespaced-skills; 149.3 → base 149-2-reserved-names.
3. No ticket comments posted, no transitions, never merged or retargeted by the engine.
Pack Deliver checks: none (no extensions.md). VERSION check: changelog.d in use, not applicable.
