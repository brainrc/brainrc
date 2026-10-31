# Log: 243-2-researcher-proof

## engine · intake, spec · done (oneshot, inline)
Child 2 of 4 of campaign-243. The parent spec is approved; this child's ACs are AC1, AC2, AC3, AC8, AC9, AC11 and AC12. Implemented inline: b908ba0.

## security-reviewer · batch · changes-requested
2 HIGH: unconstrained proof re-run; researcher Bash and Write limited by prose only. 3 MEDIUM, 3 LOW. Fix attempt 2: proof_guard.py (76a1fd4).

## security-reviewer · rereview · changes-requested
2 HIGH, both confirmed in temp dirs. (1) Allowed programs can run code: rg --pre, git grep -O, git show --ext-diff/--textconv, pytest plugins and conftest. (2) The secret-path check misses grep -r/rg -uu over .env, git show HEAD:.env and --file=.env, and symlinks escape the worktree. 3 MEDIUM, 2 LOW.

## engine · blocked (tainted stop)
2026-10-31T20:34:12Z
The retry budget (2 attempts) is used and HIGH security findings are open, so this is a tainted stop under SKILL.md § Oneshot mode: push nothing, open no PR, report locally. Children 3 and 4 are paused. Child 1 (243.1) stays verified and unpushed.

## owner · retry budget lifted once
Owner: "Narrow the proof re-run". Attempt 3 (df13959): a fixed read-only allowlist, symlink-resolved paths, no test-runner re-run, a process-group timeout, a fail-closed scan. 13 guard tests pass; suite OK.

## security-reviewer · rereview-2 · changes-requested
Every earlier bypass is closed. New: 1 HIGH (bare `git show <rev>` prints the patch, so a committed .env leaks), 1 MEDIUM (secret list misses id_rsa/.ssh/*.pem/.git/config), 4 LOW.

## engine · blocked again (tainted stop)
2026-10-31T23:39:32Z
The engine stops, as promised to the owner: a HIGH is open after the extra attempt. Nothing pushed.
